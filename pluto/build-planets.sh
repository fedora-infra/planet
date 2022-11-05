#!/bin/sh

GALAXY='/pluto/builds'

mkdir -p /root/.pluto/
mv template/ /root/.pluto/planet

pushd $GALAXY
for PLANET in design desktop edited people quality security summer-coding; do
    if [ "$PLANET" = "people" ]; then
        pluto build $PLANET.ini -o /var/www/html/ -d /var/www/html/ -t planet 
    else
        mkdir /var/www/html/$PLANET 
        ln -s /var/www/html/css-v2 /var/www/html/$PLANET/css-v2
        ln -s /var/www/html/images-v2 /var/www/html/$PLANET/images-v2
        pluto build $PLANET.ini -o /var/www/html/$PLANET -d /var/www/html/$PLANET -t planet 
    fi
done
popd
