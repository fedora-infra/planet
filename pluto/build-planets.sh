#!/bin/sh

GALAXY='/pluto/builds'

# for PLANET in design desktop edited  people  quality  security  summer-coding; do
#     if [ "$PLANET" = "people" ]; then
#         pushd $GALAXY/$PLANET
#         pluto build planet.ini -o /var/www/html/ -d /var/www/html/ -t $PLANET
#         popd
#     else
#         mkdir /var/www/html/$PLANET 
#         ln -s /var/www/html/css-v2 /var/www/html/$PLANET/css-v2
#         ln -s /var/www/html/images-v2 /var/www/html/$PLANET/images-v2
#         pushd $GALAXY/$PLANET
#         pluto build planet.ini -o /var/www/html/$PLANET -d /var/www/html/$PLANET -t $PLANET
#         popd
#     fi
# done

# Lines below just for testing
pushd $GALAXY/people
pluto build planet.ini -o /var/www/html/ -d /var/www/html/ -t people
popd

# for testing purposes, TODO: fix above loop
pushd $GALAXY/design
mkdir /var/www/html/design
ln -s /var/www/html/css-v2 /var/www/html/design/css-v2
ln -s /var/www/html/images-v2 /var/www/html/design/images-v2
pluto build planet.ini -o /var/www/html/design -d /var/www/html/design -t design
popd

httpd -D FOREGROUND &