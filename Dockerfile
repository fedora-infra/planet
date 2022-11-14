FROM fedora:36

RUN dnf update -y && dnf install -y httpd rubygems gcc sqlite-devel ruby-devel

COPY site site
COPY pluto pluto

WORKDIR /pluto
RUN bundle install
RUN ./build-planets.sh

WORKDIR /
RUN mv site/* /var/www/html/

EXPOSE 80

ENTRYPOINT ["/usr/sbin/httpd"]
CMD ["-D","FOREGROUND"]
