#!/usr/bin/python3

import subprocess
import requests
import hashlib
import os
import shutil

import fasjson_client


build_dir = "/pluto/build"
fedora_planet_url_prod = "planet.apps.ocp.fedoraproject.org"
fedora_planet_url_stg = "planet.apps.ocp.stg.fedoraproject.org"

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
if not os.path.exists("/var/www/html/images-v2"):
    shutil.move("/pluto/images-v2", "/var/www/html/")
if not os.path.exists("/var/www/html/css-v2"):
    shutil.move("/pluto/css-v2", "/var/www/html/")

subprocess.call("rm -rf " + build_dir, shell=True)
subprocess.run(["mkdir", "-p", build_dir])

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

# writing headers ini file -> pluto use this to create tables in SQLite
with open(f"{build_dir}/planet.ini", "a") as f:
    f.write("title = Fedora People\n")
    f.write(f"url = {fedora_planet_url_prod}\n\n")
    f.write(std_people_ini_content + "\n")

# append users blog in ini file
while True:
    for user in fasjson_response.result:
        for rssindex, rssurl in enumerate(user["rssurls"]):
            if rssurl.startswith("http://"):
                print(f"User {user['username']} has a bad RSS URL: {rssurl}")
                continue
            try:
                r = requests.get(rssurl)

                if r.status_code == 200:
                    with open(f"{build_dir}/planet.ini", "a") as f:
                        f.write(f"[{user['username']}_{rssindex + 1}]\n  ")
                        f.write(f"name = {user['human_name']}\n  ")
                        try:
                            f.write(f"link = {user['websites'][0]}\n  ")
                        except (TypeError, IndexError):
                            # It can be either None (TypeError) or an empty list (IndexError)
                            print(
                                f"User {user['username']} has a RSS URL but no website."
                            )
                        f.write(f"feed = {rssurl}\n  ")
                        f.write(
                            f"avatar = https://www.libravatar.org/avatar/{hashlib.md5(user['emails'][0].encode()).hexdigest()}\n  "
                        )
                        f.write(f"author = {user['username']}\n\n")
            except Exception as e:
                print(e)
    try:
        fasjson_response = fasjson_response.next_page()
    except fasjson_client.response.PaginationError:
        break

# build planet with pluto
subprocess.call(
    f"cd /pluto; pluto build {build_dir}/planet.ini -o /var/www/html -d /var/www/html -t planet",
    shell=True,
)
