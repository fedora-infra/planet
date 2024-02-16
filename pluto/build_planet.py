#!/usr/bin/python3

import subprocess
import json
import requests
import hashlib
import os


build_dir = "/pluto/build"
fedora_planet_url_prod = "planet.apps.ocp.fedoraproject.org"
fedora_planet_url_stg = "planet.apps.ocp.stg.fedoraproject.org"

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

if os.environ.get('OPENSHIFT_BUILD_REFERENCE') == 'staging':
  subprocess.call(f'kinit -kt {os.environ.get('KRB5_CLIENT_KTNAME')} HTTP/{fedora_planet_url_stg}@STG.FEDORAPROJECT.ORG', shell=True)

  users = json.loads(
    subprocess.check_output(
      f"/usr/bin/curl -u : --negotiate 'https://fasjson.stg.fedoraproject.org/v1/groups/fedora-contributor/members/' -H 'X-Fields: username,human_name,website,rssurl,emails'",
      shell=True,
      text=True
    )
  )
else:
  subprocess.call(f'kinit -kt {os.environ.get('KRB5_CLIENT_KTNAME')} HTTP/{fedora_planet_url_prod}@FEDORAPROJECT.ORG', shell=True)

  users = json.loads(
    subprocess.check_output(
      f"/usr/bin/curl -u : --negotiate 'https://fasjson.fedoraproject.org/v1/groups/fedora-contributor/members/' -H 'X-Fields: username,human_name,website,rssurl,emails'",
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
  if user['rssurl'] != None:
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
