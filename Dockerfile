FROM fedora:38

RUN dnf update -y && \
    dnf install -y httpd rubygems gcc sqlite-devel ruby-devel python3-pip fedora-packager-kerberos python3-fasjson-client && \
    pip3 install requests fedora-messaging && \
    dnf clean all 

COPY pluto pluto

RUN mkdir -p /etc/fedora-messaging /etc/pki/fedora-messaging && \
    sed -i 's/Listen 80$/Listen 8080/g' /etc/httpd/conf/httpd.conf && \
    chgrp -R 0 /run/httpd /var/www/html /pluto /etc/fedora-messaging && \
    chmod -R g+rwX /etc/httpd /var/log/httpd /run/httpd /var/www/html /pluto /etc/fedora-messaging && \
    chmod +x /pluto/build_planet.py

COPY pluto/config.toml /etc/fedora-messaging/config.toml 

WORKDIR /pluto
RUN bundle install

EXPOSE 8080

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D","FOREGROUND","-f","/etc/httpd/conf/httpd.conf"]
