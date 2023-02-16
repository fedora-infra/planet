FROM fedora:37

RUN dnf update -y && \
    dnf install -y httpd rubygems gcc sqlite-devel ruby-devel && \
    dnf clean all 

RUN sed -i 's/Listen 80$/Listen 8080/g' /etc/httpd/conf/httpd.conf && \
    chgrp -R 0 /run/httpd && \
    chmod -R g+rwX /etc/httpd /var/log/httpd /run/httpd

COPY site site
COPY pluto pluto

WORKDIR /pluto
RUN bundle install
RUN ./build-planets.sh

WORKDIR /
RUN mv site/* /var/www/html/

EXPOSE 8080

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D","FOREGROUND","-f","/etc/httpd/conf/httpd.conf"]
