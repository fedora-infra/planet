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
import configparser
from argparse import ArgumentParser
from pathlib import Path

import backoff
import fasjson_client
from fedora_messaging import api
from fedora_messaging.exceptions import ConnectionException, PublishException
from fedora_planet_messages import PostNew, Build


logger = logging.getLogger(__name__)

fedora_planet_url = "fedoraplanet.org"

if os.environ.get("OPENSHIFT_BUILD_REFERENCE") == "staging":
    fedora_planet_url = f"stg.{fedora_planet_url}"
    env = "STG."
else:
    env = ""


def _add_basic_config(ini_content):
    ini_content.read_dict(
        {
            "fedorauniversity": {
                "name": "Fedora University Tour",
                "link": "https://fedorauniversity.wordpress.com",
                "feed": "https://fedorauniversity.wordpress.com/feed/",
                "avatar": f"https://{fedora_planet_url}/images-v2/heads/default.png",
                "author": "admin",
            },
            "fedoramagazine": {
                "name": "Fedora Magazine",
                "link": "https://fedoramagazine.org",
                "feed": "https://fedoramagazine.org/?feed=rss2",
                "avatar": f"https://{fedora_planet_url}/images-v2/heads/planet-magazine.png",
                "author": "admin",
            },
            "fedora-badges": {
                "name": "Fedora Badges",
                "link": "https://badges.fedoraproject.org",
                "feed": "https://badges.fedoraproject.org/explore/badges/rss",
                "avatar": f"https://{fedora_planet_url}/images-v2/heads/default.png",
                "author": "admin",
            },
            "fedora-status": {
                "name": "Fedora Infrastructure Status",
                "link": "https://status.fedoraproject.org",
                "feed": "https://status.fedoraproject.org/changes.rss",
                "avatar": f"https://{fedora_planet_url}/images-v2/heads/default.png",
                "author": "admin",
            },
            "community-blog": {
                "name": "Fedora Community Blog",
                "link": "https://communityblog.fedoraproject.org",
                "feed": "https://communityblog.fedoraproject.org/?feed=rss",
                "avatar": f"https://{fedora_planet_url}/images-v2/heads/default.png",
                "author": "admin",
            },
        }
    )
    return ini_content


def build_ini_file(ini_file, ini_content):
    _add_basic_config(ini_content)

    # Kerberos login
    subprocess.call(
        f'kinit -kt {os.environ.get("KRB5_CLIENT_KTNAME")} HTTP/{fedora_planet_url}@{env}FEDORAPROJECT.ORG',
        shell=True,
    )

    for user_section in _get_user_sections():
        ini_content.read_dict(user_section)

    os.makedirs(os.path.dirname(ini_file))
    # writing headers ini file -> pluto use this to create tables in SQLite
    with open(ini_file, "w") as f:
        f.write("title = Fedora People\n")
        f.write(f"url = {fedora_planet_url}\n\n")
        ini_content.write(f)


def _get_user_sections():
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

    # append users blog in ini file
    while True:
        for user in fasjson_response.result:
            logger.info("Adding user %s", user["username"])
            for rssindex, rssurl in enumerate(user["rssurls"]):
                if rssurl.startswith("http://"):
                    logger.warning(
                        f"User {user['username']} has a bad RSS URL: {rssurl}"
                    )
                    continue
                try:
                    r = requests.get(rssurl)

                    if r.status_code == 200:
                        section = f"{user['username']}_{rssindex + 1}"
                        avatar_hash = hashlib.md5(
                            user["emails"][0].encode()
                        ).hexdigest()
                        content = {
                            "name": user["human_name"],
                            "feed": rssurl,
                            "author": user["username"],
                            "avatar": f"https://www.libravatar.org/avatar/{avatar_hash}",
                        }
                        try:
                            content["link"] = user["websites"][0]
                        except (TypeError, IndexError):
                            # It can be either None (TypeError) or an empty list (IndexError)
                            logger.warning(
                                f"User {user['username']} has a RSS URL but no website."
                            )
                        yield {section: content}
                except Exception:
                    logger.exception("Error when requesting RSS URL")
        try:
            fasjson_response = fasjson_response.next_page()
        except fasjson_client.response.PaginationError:
            logger.error("Fasjson client pagination error")
            break


def _call_pluto(ini_file, dest_dir):
    logger.info("Building planet with pluto")
    dest_dir = Path(dest_dir).absolute()
    if not dest_dir.exists():
        dest_dir.mkdir()
    for static_dir in ("images-v2", "css-v2"):
        static_path = dest_dir.joinpath(static_dir)
        if not static_path.exists():
            shutil.copytree(os.path.join("pluto", static_dir), static_path.as_posix())
    try:
        subprocess.call(
            [
                "pluto",
                "build",
                ini_file,
                "-o",
                dest_dir.as_posix(),
                "-d",
                dest_dir.as_posix(),
                "-t",
                "planet",
            ],
            cwd="pluto",
        )
    except Exception:
        logger.exception("Error during the pluto build")


def _backoff_hdlr(details):
    logger.warning(
        "Publishing message failed. Retrying. %s",
        traceback.format_tb(sys.exc_info()[2]),
    )


def _giveup_hdlr(details):
    logger.error(
        "Publishing message failed. Giving up. %s",
        traceback.format_tb(sys.exc_info()[2]),
    )


@backoff.on_exception(
    backoff.expo,
    (ConnectionException, PublishException),
    max_tries=3,
    on_backoff=_backoff_hdlr,
    on_giveup=_giveup_hdlr,
)
def publish(message):
    api.publish(message)


def _send_fedora_messages(dest_dir, after):
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


def _send_final_message(ini_content):
    planet_users = {
        section: dict(ini_content.items(section))
        for section in ini_content.sections()
        if section is not configparser.UNNAMED_SECTION
    }
    try:
        publish(
            Build(
                body={
                    "title": ini_content.get(configparser.UNNAMED_SECTION, "title"),
                    "url": ini_content.get(configparser.UNNAMED_SECTION, "url"),
                    "Users": planet_users,
                }
            )
        )
    except Exception:
        logger.exception("Error when trying to publish message")


def main():
    # Arguments
    parser = ArgumentParser()
    parser.add_argument(
        "-b", "--build-dir", default="/pluto/build", help="build directory"
    )
    parser.add_argument(
        "-o", "--output-dir", default="/var/www/html", help="output directory"
    )
    parser.add_argument("-l", "--log-dir", help="log directory")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="display more info"
    )
    parser.add_argument("--skip-ini", action="store_true")
    parser.add_argument("--skip-pluto", action="store_true")
    args = parser.parse_args()

    # Logging
    handlers = [
        logging.StreamHandler(sys.stdout),
    ]
    if args.log_dir:
        handlers.append(logging.FileHandler(os.path.join(args.log_dir, "build.log")))
    logging.basicConfig(
        handlers=handlers,
        encoding="utf-8",
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y/%m/%d %I:%M:%S %p",
    )

    ini_file = Path(args.build_dir).joinpath("planet.ini").absolute().as_posix()
    ini_content = configparser.ConfigParser(allow_unnamed_section=True)
    if args.skip_ini:
        ini_content.read(ini_file)
    else:
        build_ini_file(ini_file, ini_content)

    # build planet with pluto
    start_time = datetime.datetime.now(tz=datetime.timezone.utc)
    if not args.skip_pluto:
        _call_pluto(ini_file, args.output_dir)

    # send to fedora messaging
    _send_fedora_messages(dest_dir=args.output_dir, after=start_time)
    _send_final_message(ini_content)


if __name__ == "__main__":
    main()
