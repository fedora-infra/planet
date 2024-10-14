#!/bin/bash

truncate --size=0 /etc/httpd/logs/access_log /etc/httpd/logs/error_log /var/log/planet/build.log
tail -qf /etc/httpd/logs/access_log /etc/httpd/logs/error_log /var/log/planet/build.log &
exec /usr/sbin/httpd -D FOREGROUND -f /etc/httpd/conf/httpd.conf
