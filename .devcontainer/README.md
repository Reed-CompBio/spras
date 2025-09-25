# SPRAS devcontainer

The attached [devcontainer](https://containers.dev/) contains docker-in-docker and anaconda,
with extra utilities for building Apptainer. Good for problems with installing any three of these tools,
but Podman currently does not work within this devcontainer.

Devcontainers can be launched in Visual Studio Code (not VSCodium!), through [JetBrains Gateway](https://www.jetbrains.com/remote-development/gateway/),
through [GitHub Codespaces](https://github.com/features/codespaces), a [coder](https://coder.com/) instance,
or with [GitPod](https://www.gitpod.io/docs/gitpod/configuration/devcontainer/overview).

## Building Apptainer

Since building apptainer takes a while, we leave building apptainer as an external script one can run
inside the devcontainer, but `go` and other necessary dependencies to build `apptainer` are already present in
the devcontainer Dockerfile.

Below is a shell script which will do the entire installation for you (but it will change your
shell's CWD):

```sh
cd /
# sudo is required since we are in root
sudo git clone https://github.com/apptainer/apptainer.git
# but we would like to use apptainer normally
sudo chown -R $(whoami): /apptainer/
cd /apptainer
git checkout v1.4.2 # pin version
./mconfig --without-libsubid --with-suid # --without-libsubid is a dev container limitation
cd $(/bin/pwd)/builddir
make
sudo make install
```

After this, run `apptainer` to confirm your installation.
