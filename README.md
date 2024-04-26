# Fedora Planet

Fedora Planet is a distributed communication tool that many Fedora contributors rely on to keep a pulse on Fedora's community. Contributors connect their blogs to Planet Fedora to express to the Fedora community their thoughts and personality as they relate to our project, and to share what they are working on in Fedora through blog posts. [[Wiki](https://fedoraproject.org/wiki/Planet)]


## Getting Started

Fedora Planet is using [pluto](https://github.com/feedreader/pluto) as a feed reader and is currently running on Openshift (OCP) in [staging](https://planet.apps.ocp.stg.fedoraproject.org/) and [produção](https://planet.apps.ocp.fedoraproject.org/).

All modifications are applied through [Ansible](https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/planet). The build is done by running the `build_planets.py` script, which is scheduled in cron, with the output files located in site/.

The script `build_planets.py` has, by default, references to official Fedora sites such as Fedora Magazine, badges, status, etc., and it uses queries through fasjson to collect the sites that users have added to their page on [Fedora Accounts](https://accounts.fedoraproject.org/).

As it's provisioned on OCP, the Python script that executes the Pluto build is utilizing the environment variable `OPENSHIFT_BUILD_REFERENCE`.


Additionally, Pluto templates are stored in pluto/template, and it builds files that are pointed to in the .txt file.

```
# Planet template manifest

<Name of the file>  <Name of the template file>
```

## Running locally

To provision the container go to the `Dockerfile` directory and run the following commands:

```sh
$ sudo podman build -t <image name>:<image version> .
$ sudo podman run -dit --name <container name> -p 8080:80 <image name>:<image version>
```

When its done the container will be running the Fedora Planet website.
Go to the web browser and see it working by navigating to `localhost:8080`.

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (git checkout -b feature/AmazingFeature)
3. Commit your Changes (git commit -sm 'Add some AmazingFeature')
4. Push to the Branch (git push origin feature/AmazingFeature)
5. Open a Pull Request
