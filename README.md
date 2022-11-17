# Fedora Planet

This repo contains Fedora Planet website. Fedora Planet is a distributed communication tool that many Fedora contributors rely on to keep a pulse on Fedora's community. Contributors connect their blogs to Planet Fedora to express to the Fedora community their thoughts and personality as they relate to our project, and to share what they are working on in Fedora through blog posts. [[Wiki](https://fedoraproject.org/wiki/Planet)]

## Getting Started

Fedora Planet is under development now and its feedreader is being migrated from [venus](https://github.com/rubys/venus) to [pluto](https://github.com/feedreader/pluto).

To provision the container go to the `Dockerfile` directory and run the following commands:

```sh
$ sudo podman build -t <image name>:<image version> .
$ sudo podman run -dit --name <container name> -p 8080:80 <image name>:<image version>
```

When its done the container will be running the Fedora Planet website.
Go to the web browser and see it working by navigating to `localhost:8080`.

## How it works

Pluto templates are stored in `pluto/template`, it builds files that are pointed to in the `.txt` file.

```
# Planet template manifest

<Name of the file>  <Name of the template file>
```

The script `build-planets.sh` should build Fedora planets and output the files in `site/`
