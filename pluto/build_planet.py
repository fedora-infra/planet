#!/usr/bin/python3

import subprocess
import requests
import hashlib
import os
import shutil
import logging
import datetime
import sqlite3
import traceback
import sys

import backoff
import fasjson_client
from fedora_messaging import api
from fedora_messaging.exceptions import ConnectionException, PublishException
from fedora_planet_messages import PostNew


build_dir = os.getenv("PLANET_BUILD_DIR", "/pluto/build")
dest_dir = os.getenv("PLANET_DEST_DIR", "/var/www/html")
log_dir = os.getenv("PLANET_LOG_DIR", "/var/log/planet")

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=os.path.join(log_dir, "build.log"),
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %I:%M:%S %p",
)
fedora_planet_url_prod = "fedoraplanet.org"
fedora_planet_url_stg = "stg.fedoraplanet.org"

if os.environ.get("OPENSHIFT_BUILD_REFERENCE") == "staging":
    fedora_planet_url = fedora_planet_url_stg
    env = "STG."
else:
    fedora_planet_url = fedora_planet_url_prod
    env = ""

std_people_ini_content = f"""
[fedorauniversity]
  name = Fedora University Tour
  link = https://fedorauniversity.wordpress.com
  feed = https://fedorauniversity.wordpress.com/feed/
  avatar = https://{fedora_planet_url}/images-v2/heads/default.png
  author = admin

[fedoramagazine]
  name = Fedora Magazine
  link = https://fedoramagazine.org
  feed = https://fedoramagazine.org/?feed=rss2
  avatar = https://{fedora_planet_url}/images-v2/heads/planet-magazine.png
  author = admin

[fedora-badges]
  name = Fedora Badges
  link = https://badges.fedoraproject.org
  feed = https://badges.fedoraproject.org/explore/badges/rss
  avatar = https://{fedora_planet_url}/images-v2/heads/default.png
  author = admin

[fedora-status]
  name = Fedora Infrastructure Status
  link = https://status.fedoraproject.org
  feed = https://status.fedoraproject.org/changes.rss
  avatar = https://{fedora_planet_url}/images-v2/heads/default.png
  author = admin

[community-blog]
  name = Fedora Community Blog
  link = https://communityblog.fedoraproject.org
  feed = https://communityblog.fedoraproject.org/?feed=rss
  avatar = https://{fedora_planet_url}/images-v2/heads/default.png
  author = admin
"""

# Reset directories
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
for static_dir in ("images-v2", "css-v2"):
    if not os.path.exists(os.path.join(dest_dir, static_dir)):
        shutil.copytree(
            os.path.join("pluto", static_dir), os.path.join(dest_dir, static_dir)
        )

shutil.rmtree(build_dir)
os.makedirs(build_dir)

# Kerberos login
subprocess.call(
    f'kinit -kt {os.environ.get("KRB5_CLIENT_KTNAME")} HTTP/{fedora_planet_url}@{env}FEDORAPROJECT.ORG',
    shell=True,
)

# Get data from fasjson
fasjson = fasjson_client.Client(f"https://fasjson.{env.lower()}fedoraproject.org")
fasjson_response = fasjson.search(
    rssurl="*",
    group=["fedora-contributor"],
    _request_options={
        "headers": {
            "X-Fields": ["username", "human_name", "websites", "rssurls", "emails"]
        }
    },
)

ini_file = os.path.join(build_dir, "planet.ini")
# writing headers ini file -> pluto use this to create tables in SQLite
with open(ini_file, "a") as f:
    f.write("title = Fedora People\n")
    f.write(f"url = {fedora_planet_url_prod}\n\n")
    f.write(std_people_ini_content + "\n")

# append users blog in ini file
while True:
    for user in fasjson_response.result:
        logger.info("Adding user %s", user["username"])
        for rssindex, rssurl in enumerate(user["rssurls"]):
            if rssurl.startswith("http://"):
                logger.warning(f"User {user['username']} has a bad RSS URL: {rssurl}")
                continue
            try:
                r = requests.get(rssurl)

                if r.status_code == 200:
                    with open(ini_file, "a") as f:
                        f.write(f"[{user['username']}_{rssindex + 1}]\n  ")
                        f.write(f"name = {user['human_name']}\n  ")
                        try:
                            f.write(f"link = {user['websites'][0]}\n  ")
                        except (TypeError, IndexError):
                            # It can be either None (TypeError) or an empty list (IndexError)
                            logger.warning(
                                f"User {user['username']} has a RSS URL but no website."
                            )
                        f.write(f"feed = {rssurl}\n  ")
                        f.write(
                            f"avatar = https://www.libravatar.org/avatar/{hashlib.md5(user['emails'][0].encode()).hexdigest()}\n  "
                        )
                        f.write(f"author = {user['username']}\n\n")
            except Exception:
                logger.exception("Error when requesting RSS URL")
    try:
        fasjson_response = fasjson_response.next_page()
    except fasjson_client.response.PaginationError:
        logger.error("Fasjson client pagination error")
        break


def backoff_hdlr(details):
    logger.warning(
        "Publishing message failed. Retrying. %s",
        traceback.format_tb(sys.exc_info()[2]),
    )


def giveup_hdlr(details):
    logger.error(
        "Publishing message failed. Giving up. %s",
        traceback.format_tb(sys.exc_info()[2]),
    )


@backoff.on_exception(
    backoff.expo,
    (ConnectionException, PublishException),
    max_tries=3,
    on_backoff=backoff_hdlr,
    on_giveup=giveup_hdlr,
)
def publish(message):
    api.publish(message)


def send_fedora_messages(after):
    db_con = sqlite3.connect(os.path.join(dest_dir, "planet.db"))
    with db_con:
        cursor = db_con.cursor()
        result = cursor.execute(
            """
            SELECT f.author, f.avatar, f.auto_title, i.title, i.url
            FROM items i JOIN feeds f ON i.feed_id = f.id
            WHERE i.created_at > ? ORDER BY i.created_at ;
            """,
            (after.isoformat(sep=" "),),
        )
        for row in result:
            message = PostNew(
                topic="planet.post.new",
                body={
                    "username": row[0],
                    "face": row[1],
                    "name": row[2],
                    "post": {
                        "title": row[3],
                        "url": row[4],
                    },
                },
            )
            logger.info(f"Sending message {message.id}: {message}")
            publish(message)


# build planet with pluto
logger.info("Building planet with pluto")
start_time = datetime.datetime.now(tz=datetime.timezone.utc)
try:
    subprocess.call(
        ["pluto", "build", ini_file, "-o", dest_dir, "-d", dest_dir, "-t", "planet"],
        cwd="pluto",
    )
except Exception:
    logger.exception("Error during the pluto build")

# send to fedora messaging
send_fedora_messages(after=start_time)

planet_users = dict()
username = None
with open(f"{build_dir}/planet.ini", "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            username = line[1:-1]
            planet_users[username] = dict()
        elif username is not None:
            key, value = line.split("=", 1)
            planet_users[username][key.strip()] = value.strip()

try:
    publish(api.Message(topic="planet.build", body={"Users": planet_users}))
except Exception:
    logger.exception("Error when trying to publish message")
