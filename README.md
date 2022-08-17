# Fedora Planet

This repo contains Fedora Planet website. Fedora Planet is a distributed communication tool that many Fedora contributors rely on to keep a pulse on Fedora's community. Contributors connect their blogs to Planet Fedora to express to the Fedora community their thoughts and personality as they relate to our project, and to share what they are working on in Fedora through blog posts. [[Wiki](https://fedoraproject.org/wiki/Planet)]

## Getting Started

Fedora Planet is under development now and it's feedreader is being migrated from venus to pluto
To provision the container go to the `Dockerfile` directory and run the following commands:

```sh
$ sudo podman build -t <image name>:<image version> .
$ sudo podman run -it --name <container name> -p 8080:80 <image name>:<image version>
```

When its over you will be in the container. Run apache:

```sh
httpd -D FOREGROUND
```

Then go to the web browser and see how it's running by typing `localhost:8080` in the URL.

## How it works

Pluto stores templates at `.pluto` under user's home path, it builds files that are pointed in `.txt` file

```
# Planet template manifest

<Name of the file>  <Name of the template file>
```

The script `build-planets.sh` should build Fedora planets and output the files in `/var/www/html/`
