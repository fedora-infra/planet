FROM fedora:36

RUN dnf update -y && dnf install -y httpd rubygems gcc sqlite-devel ruby-devel 
RUN mkdir -p /srv/planet/ /root/.pluto/

COPY site /var/www/html/
COPY pluto pluto

WORKDIR /pluto
RUN bundle install 
# TO DO: Change line below when more templates are created
RUN mv templates/people /root/.pluto/ 
RUN ./build-planets.sh
EXPOSE 80

# Running shell for testing purpose

# ENTRYPOINT ["/usr/sbin/httpd"] 
# CMD ["-D","FOREGROUND"]
CMD /bin/sh
