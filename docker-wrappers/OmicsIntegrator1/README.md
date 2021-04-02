# Omics Integrator 1 Docker image

A Docker image for [Omics Integrator](https://github.com/fraenkel-lab/OmicsIntegrator).

The base environment was created by interactively following the [test setup](https://github.com/fraenkel-lab/OmicsIntegrator/blob/0a57ede6beeef6e63b86d19898e560d62015e85d/.travis.yml) in a Docker container.
The conda environment contained the packages
```
# Name                    Version                   Build  Channel
_libgcc_mutex             0.1                        main
atomicwrites              1.4.0                    pypi_0    pypi
attrs                     20.3.0                   pypi_0    pypi
backports-functools-lru-cache 1.6.3                    pypi_0    pypi
ca-certificates           2021.1.19            h06a4308_1
certifi                   2020.6.20          pyhd3eb1b0_3
configparser              4.0.2                    pypi_0    pypi
contextlib2               0.6.0.post1              pypi_0    pypi
cycler                    0.10.0                   pypi_0    pypi
decorator                 4.4.2                    pypi_0    pypi
funcsigs                  1.0.2                    pypi_0    pypi
importlib-metadata        2.1.1                    pypi_0    pypi
kiwisolver                1.1.0                    pypi_0    pypi
libffi                    3.3                  he6710b0_2
libgcc-ng                 9.1.0                hdf63c60_0
libstdcxx-ng              9.1.0                hdf63c60_0
matplotlib                2.2.5                    pypi_0    pypi
more-itertools            5.0.0                    pypi_0    pypi
ncurses                   6.2                  he6710b0_1
networkx                  1.11                     pypi_0    pypi
numpy                     1.13.3                   pypi_0    pypi
packaging                 20.9                     pypi_0    pypi
pathlib2                  2.3.5                    pypi_0    pypi
pip                       19.3.1                   py27_0
pluggy                    0.13.1                   pypi_0    pypi
py                        1.10.0                   pypi_0    pypi
pyparsing                 2.4.7                    pypi_0    pypi
pytest                    2.9.2                    pypi_0    pypi
python                    2.7.18               h15b4118_1
python-dateutil           2.8.1                    pypi_0    pypi
pytz                      2021.1                   pypi_0    pypi
readline                  8.1                  h27cfd23_0
scandir                   1.10.0                   pypi_0    pypi
scipy                     0.19.1                   pypi_0    pypi
setuptools                44.0.0                   py27_0
six                       1.15.0                   pypi_0    pypi
sqlite                    3.35.2               hdfb4753_0
subprocess32              3.5.4                    pypi_0    pypi
tk                        8.6.10               hbc83047_0
wcwidth                   0.2.5                    pypi_0    pypi
wheel                     0.36.2             pyhd3eb1b0_0
zipp                      1.2.0                    pypi_0    pypi
zlib                      1.2.11               h7b6447c_3
```

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t agitter/omics-integrator-1 -f Dockerfile .
```

To confirm that commands are run inside the conda environment run:
```
winpty docker run agitter/omics-integrator-1 conda list
```
The `winpty` prefix is only needed on Windows.

## Testing
The `input` directory contains test files `oi1-edges.txt` and `oi2-prizes.txt`.
The Docker wrapper can be tested with the command
```
python test-oi1.py
```

The Docker wrapper also can be tested by running the Omics Integrator tests interactively:
```
winpty docker run -it agitter/omics-integrator-1 bash
conda activate oi1
python setup.py test -a "--msgpath=$MSGSTEINER_PATH"
```

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator
- Attribute http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz and discuss permission to distribute
- Optimize order of commands in Dockerfile
- Delete data files
- Document usage, required packages
- Remove testing and setup packages from environment if not needed
- Determine how to use MSGSTEINER_PATH when passing in commands, fix ENTRYPOINT and/or CMD
- Decide what to use for working directory and where to map input data
