FROM fedora:37

RUN dnf update -y && \
    dnf install -y httpd rubygems gcc sqlite-devel ruby-devel python3-pip fedora-packager-kerberos && \
    pip3 install requests && \
    dnf clean all 

RUN sed -i 's/Listen 80$/Listen 8080/g' /etc/httpd/conf/httpd.conf && \
    chgrp -R 0 /run/httpd && \
    chmod -R g+rwX /etc/httpd /var/log/httpd /run/httpd

COPY site site
COPY pluto pluto
ADD krb5/krb5.conf /etc/

WORKDIR /pluto
RUN python3 create_build_files.py
RUN bundle install
RUN ./build-planets.sh

WORKDIR /
RUN mv site/* /var/www/html/

EXPOSE 8080

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D","FOREGROUND","-f","/etc/httpd/conf/httpd.conf"]
