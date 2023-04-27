#!/usr/bin/python3

import subprocess
import json
import requests
import hashlib


build_dir = "build/"
fedora_planet_url = "https://fedoraplanet.org/"

# This dict relates the fas group name as key to get its users and the file and url content as value that pluto will use to build
# TODO: check if all those groups are still necessary because the subplanets were droped
fas_groups = {
  "designteam": {
    "title": "Fedora Design Team Planet",
    "planet_url": fedora_planet_url + "design",
    "build_file": "design.ini",
  },
  # TODO: create desktop group in fedora accounts to update this script
  # "<fas_desktop_group_name>": {
  #   "title": "Fedora Desktop Planet",
  #   "planet_url": fedora_planet_url + "desktop",
  #   "build_file": "desktop.ini",
  # },
  "fedora-contributor": {
    "title": "Fedora People",
    "planet_url": fedora_planet_url,
    "build_file": "people.ini",
  },
  "qa": {
    "title": "Fedora Quality Planet",
    "planet_url": fedora_planet_url + "quality",
    "build_file": "quality.ini",
  },
  "security-team": {
    "title": "Fedora Security Planet",
    "planet_url": fedora_planet_url + "security",
    "build_file": "security.ini",
  },
  "summer-coding": {
    "title": "Fedora summer-coding Planet",
    "planet_url": fedora_planet_url + "summer-coding",
    "build_file": "summercoding.ini",
  },
}

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

# TODO: check if this loop is still necessary because the subplanets were droped
for fas_group,info in fas_groups.items():
  # get users that are in the group
  users = json.loads(
    subprocess.check_output(
      f"/usr/bin/curl -u : --negotiate 'https://fasjson.fedoraproject.org/v1/groups/{fas_group}/members/?page_number=1' -H 'X-Fields: username,human_name,website,emails'",
      shell=True,
      text=True
    )
  )

  # writing headers for each ini file -> pluto use this to create tables in SQLite
  with open(build_dir + info['build_file'], "a") as f:
    f.write(f"title = {info['title']}\n")
    f.write(f"url = {info['planet_url']}\n\n")

    if fas_group == "fedora-contributor":
      f.write(std_people_ini_content + "\n")

  # append users blog in ini file
  for user in list(users['result']):
    if user['website'] != None:
      try:
        # TODO: get rss feed link after it gets implemented on noggin and fasjson
        r = requests.get(user['website'] + "/" + 'feed')

        if r.status_code==200:
          with open(build_dir + info['build_file'],"a") as f:
            f.write(f"[{user['username']}]\n  ")
            f.write(f"name = {user['human_name']}\n  ")
            f.write(f"link = {user['website']}\n  ")
            f.write(f"feed = {user['website']}/{word}\n  ")
            f.write(f"avatar = https://www.libravatar.org/avatar/{hashlib.md5(user['emails'][0].encode()).hexdigest()}\n  ")
            f.write(f"author = {user['username']}\n\n")
      except:
        pass

# TODO: add lines to build planet using pluto and delete build-planets.sh