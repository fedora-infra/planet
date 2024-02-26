#!/usr/bin/python3

import subprocess
import json
import requests
import hashlib
import os


build_dir = "/pluto/build"
fedora_planet_url_prod = "planet.apps.ocp.fedoraproject.org"
fedora_planet_url_stg = "planet.apps.ocp.stg.fedoraproject.org"

if os.environ.get('OPENSHIFT_BUILD_REFERENCE') == 'staging':
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
subprocess.call('rm -rf ' + build_dir, shell=True)
subprocess.run(['mkdir', '-p', build_dir])

# Kerberos login
subprocess.call(f'kinit -kt {os.environ.get("KRB5_CLIENT_KTNAME")} HTTP/{fedora_planet_url}@{env}FEDORAPROJECT.ORG', shell=True)

# Get data from fasjson
users = json.loads(
  subprocess.check_output(
    f"/usr/bin/curl -u : --negotiate 'https://fasjson.stg.fedoraproject.org/v1/groups/fedora-contributor/members/' -H 'X-Fields: username,human_name,website,rssurl,emails'",
    shell=True,
    text=True
  )
)

# writing headers ini file -> pluto use this to create tables in SQLite
with open(f"{build_dir}/planet.ini", "a") as f:
  f.write(f"title = Fedora People\n")
  f.write(f"url = {fedora_planet_url_prod}\n\n")
  f.write(std_people_ini_content + "\n")

# append users blog in ini file
for user in list(users['result']):
  if user['rssurl'] != None and user['rssurl'].split(":")[0] != 'http':
    try:
      r = requests.get(user['rssurl'])

      if r.status_code==200:
        with open(f"{build_dir}/planet.ini","a") as f:
          f.write(f"[{user['username']}]\n  ")
          f.write(f"name = {user['human_name']}\n  ")
          f.write(f"link = {user['website']}\n  ")
          f.write(f"feed = {user['rssurl']}\n  ")
          f.write(f"avatar = https://www.libravatar.org/avatar/{hashlib.md5(user['emails'][0].encode()).hexdigest()}\n  ")
          f.write(f"author = {user['username']}\n\n")
    except Exception as e:
      print(e)

# build planet with pluto
subprocess.call(f'cd /pluto; pluto build {build_dir}/planet.ini -o /var/www/html -d /var/www/html -t planet', shell=True)
