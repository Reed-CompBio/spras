# SPRAS devcontainer

The attached [devcontainer](https://containers.dev/) contains docker-in-docker and anaconda,
with extra utilities for building Singularity. Good for problems with installing any three of these tools,
but Podman currently does not work within this devcontainer.

Devcontainers can be launched in Visual Studio Code (not VSCodium!), through [JetBrains Gateway](https://www.jetbrains.com/remote-development/gateway/),
or through [GitHub Codespaces](https://github.com/features/codespaces) or your institution's [coder](https://coder.com/) instance.

## Building Singularity

Since this takes a good while, I leave building singularity as an external script one can run,
but `go` and the associated `apt` dependencies are already present in the Dockerfile.

```sh
cd /
# sudo is required since we are in root
sudo git clone --recurse-submodules https://github.com/sylabs/singularity.git
# but we would like to use singularity normally
sudo chown -R vscode: /singularity/
cd /singularity
git checkout --recurse-submodules v4.3.1 # pin version
./mconfig --without-libsubid # dev container limitation?
make -C builddir
sudo make -C builddir install
```
