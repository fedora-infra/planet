#!/usr/bin/python3

import subprocess
import json
import requests
import hashlib


build_dir = "build/"
fedora_planet_url = "https://fedoraplanet.org/"

std_people_ini_content = """
[fedorauniversity]
  name = Fedora University Tour
  link = http://fedorauniversity.wordpress.com
  feed = http://fedorauniversity.wordpress.com/feed/
  author = admin

[fedoramagazine]
  name = Fedora Magazine
  link = http://fedoramagazine.org
  feed = http://fedoramagazine.org/?feed=rss2
  avatar = http://fedoraplanet.org/images-v2/heads/planet-magazine.png
  author = admin

[fedora-badges]
  name = Fedora Badges
  link = https://badges.fedoraproject.org/explore
  feed = https://badges.fedoraproject.org/explore/badges/rss
  avatar = http://fedoraplanet.org/images-v2/heads/default.png
  author = admin

[fedora-status]
  name = Fedora Infrastructure Status
  link = http://status.fedoraproject.org
  feed = http://status.fedoraproject.org/changes.rss
  avatar = http://fedoraplanet.org/images-v2/heads/default.png
  author = admin

[community-blog]
  name = Fedora Community Blog
  link = http://communityblog.fedoraproject.org
  feed = http://communityblog.fedoraproject.org/?feed=rss
  avatar = https://communityblog.fedoraproject.org/wp-content/themes/communityblog-theme-0.02/images/communitybloglogo.png
  author = admin
"""


subprocess.call('rm -rf ' + build_dir, shell=True)
subprocess.run(['mkdir', '-p', build_dir])

users = json.loads(
  subprocess.check_output(
    f"/usr/bin/curl -u : --negotiate 'https://fasjson.fedoraproject.org/v1/groups/fedora-contributor/members/' -H 'X-Fields: username,human_name,website,rssurl,emails'",
    shell=True,
    text=True
  )
)

# writing headers ini file -> pluto use this to create tables in SQLite
with open(build_dir + "planet.ini", "a") as f:
  f.write(f"title = Fedora People\n")
  f.write(f"url = {fedora_planet_url}\n\n")
  f.write(std_people_ini_content + "\n")

# append users blog in ini file
for user in list(users['result']):
  if user['rssurl'] != None:
    try:
      r = requests.get(user['rssurl'])

      if r.status_code==200:
        with open(build_dir + 'planet.ini',"a") as f:
          f.write(f"[{user['username']}]\n  ")
          f.write(f"name = {user['human_name']}\n  ")
          f.write(f"link = {user['website']}\n  ")
          f.write(f"feed = {user['rssurl']}\n  ")
          f.write(f"avatar = https://www.libravatar.org/avatar/{hashlib.md5(user['emails'][0].encode()).hexdigest()}\n  ")
          f.write(f"author = {user['username']}\n\n")
    except Exception as e:
      print(e)

# build planet with pluto
subprocess.call(f'pluto build /pluto/build/planet.ini -o /var/www/html -d /var/www/html -t planet', shell=True)
