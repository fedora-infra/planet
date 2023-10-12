FROM fedora:38

RUN dnf update -y && \
    dnf install -y httpd rubygems gcc sqlite-devel ruby-devel python3-pip fedora-packager-kerberos && \
    pip3 install requests && \
    dnf clean all 

RUN sed -i 's/Listen 80$/Listen 8080/g' /etc/httpd/conf/httpd.conf && \
    chgrp -R 0 /run/httpd && \
    chmod -R g+rwX /etc/httpd /var/log/httpd /run/httpd

COPY site /var/www/html/
COPY pluto pluto
RUN chgrp -R 0 /pluto /var/www/html/ && \
    chmod -R g=u /pluto /var/www/html/

WORKDIR /pluto
RUN bundle install

EXPOSE 8080

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D","FOREGROUND","-f","/etc/httpd/conf/httpd.conf"]
