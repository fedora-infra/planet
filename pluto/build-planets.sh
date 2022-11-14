#!/bin/sh

GALAXY='/pluto/build'

mkdir -p /root/.pluto/
mv template/ /root/.pluto/planet

pushd $GALAXY
pluto build people.ini -o /var/www/html/ -d /var/www/html/ -t planet
for PLANET in design desktop edited quality security summer-coding; do
    mkdir /var/www/html/$PLANET
    ln -s /var/www/html/css-v2 /var/www/html/$PLANET/css-v2
    ln -s /var/www/html/images-v2 /var/www/html/$PLANET/images-v2
    pluto build $PLANET.ini -o /var/www/html/$PLANET -d /var/www/html/$PLANET -t planet
done
popd
