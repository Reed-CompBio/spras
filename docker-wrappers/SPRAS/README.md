# SPRAS Docker image

## Building Images

A Docker image for SPRAS that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/spras)
This image comes bundled with all of the necessary software packages to run SPRAS, and can be used for execution in distributed environments (like HTCondor).

To create the Docker image locally, make sure you are in this repository's root directory, and from your terminal run:

```bash
docker build -t <project name>/<image name>:<tag name> -f docker-wrappers/SPRAS/Dockerfile .
```

For example, to build this image with the intent of pushing it to DockerHub as reedcompbio/spras:v0.2.0, you'd run:
```bash
docker build -t reedcompbio/spras:v0.2.0 -f docker-wrappers/SPRAS/Dockerfile .
```

This will copy the entire SPRAS repository into the container and install SPRAS with `pip`. As such, any changes you've made to the current SPRAS repository will be reflected in version of SPRAS installed in the container. Since SPRAS
is being installed with `pip`, it's also possible to specify that you want development modules installed as well. If you're using the container for development and you want the optional `pre-commit` and `pytest` packages as well as a
spras package that receives changes without re-installation, change the
`pip` installation line to:

```bash
pip install -e .[dev]
```

This will cause changes to spras source code to update the installed package.

**Note:** This image will build for the same platform that is native to your system (i.e. amd64 or arm64). If you need to run this in a remote environment like HTCondor that is almost certainly `amd64` but you're building from Apple Silicon, it is recommended to either modify the Dockerfile to pin the platform:

```
FROM --platform=linux/amd64 almalinux:9
```

Or to temporarily override your system's default during the build, prepend your build command with:
```
DOCKER_DEFAULT_PLATFORM=linux/amd64
```

For example, to build reedcompbio/spras:v0.2.0 on Apple Silicon as a linux/amd64 container, you'd run:
```
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t reedcompbio/spras:v0.2.0 -f docker-wrappers/SPRAS/Dockerfile .
```

### Converting Docker Images to Apptainer/Singularity Images

It may be necessary in some cases to create an Apptainer image for SPRAS, especially if you intend to run your workflow using distributed systems like HTCondor. Apptainer (formerly known as Singularity) uses image files with `.sif` extensions. Assuming you have Apptainer installed, you can create your own sif image from an already-built Docker image with the following command:
```bash
apptainer build <new image name>.sif docker://<name of container on DockerHub>
```

For example, creating an Apptainer image for the `v0.2.0` SPRAS image might look like:
```bash
apptainer build spras-v0.2.0.sif docker://reedcompbio/spras:v0.2.0
```

After running this command, a new file called `spras-v0.2.0.sif` will exist in the directory where the command was run.

## Working with HTCondor

The folder `docker-wrappers/SPRAS` also contains several files that can be used to run workflows with this container on HTCondor. To use the `spras` image
in this environment, first login to an HTCondor Access Point (AP). Then, from the AP clone this repo:

```bash
git clone https://github.com/Reed-CompBio/spras.git
```

**Note:** To work with SPRAS in HTCondor, it is recommended that you build an Apptainer image instead of using Docker. See [Converting Docker Images to Apptainer/Singularity Images](#converting-docker-images-to-apptainersingularity-images) for instructions. Importantly, the Apptainer image must be built for the linux/amd64 architecture. Most HTCondor APs will have `apptainer` installed, but they may not have `docker`. If this is the case, you can build the image with Docker on your local machine, push the image to Docker Hub, and then convert it to Apptainer's `sif` format on the AP.

**Note:** It is best practice to make sure that the Snakefile you copy for your workflow is the same version as the Snakefile baked into your workflow's container image. When this workflow runs, the Snakefile you just copied will be used during remote execution instead of the Snakefile from the container. As a result, difficult-to-diagnose versioning issues may occur if the version of SPRAS in the remote container doesn't support the Snakefile on your current branch. The safest bet is always to create your own image so you always know what's inside of it.

There are currently two options for running SPRAS with HTCondor. The first is to submit all SPRAS jobs to a single remote Execution Point (EP). The second
is to use the Snakemake HTCondor executor to parallelize the workflow by submitting each job to its own EP.

### Submitting All Jobs to a Single EP

Navigate to the `spras/docker-wrappers/SPRAS` directory and create the `logs/` directory (`mkdir logs`). Next, modify `spras.sub` so that it uses the SPRAS apptainer image you created:
```
container_image = < your spras image >.sif
```

Then run `condor_submit spras.sub`, which will submit SPRAS to HTCondor as a single job with as many cores as indicated by the `NUM_PROCS` line in `spras.sub`, using the value of `EXAMPLE_CONFIG` as the SPRAS
configuration file. Note that you can alter the configuration file to test various workflows, but you should leave `unpack_singularity = true`, or it
is likely the job will be unsuccessful. By default, the `example_config.yaml` runs everything except for `cytoscape`, which appears to fail periodically
in HTCondor.

**Note**: The `spras.sub` submit file is an example of how this workflow could be submitted from a CHTC Access Point (AP) to the OSPool. To run in the local
CHTC pool, omit the `+WantGlideIn` and `requirements` lines

### Submitting Parallel Jobs

Parallelizing SPRAS workflows with HTCondor requires the same setup as the previous section, but with two additions. First, it requires an activated SPRAS conda environment with a `pip install`-ed version of the SPRAS module (see the main `README.md` for detailed instructions on pip installation of SPRAS).

Second, it requires an experimental executor for HTCondor that has been forked from the upstream [HTCondor Snakemake executor](https://github.com/htcondor/snakemake-executor-plugin-htcondor).

After activating your `spras` conda environment and `pip`-installing SPRAS, you can install the HTCondor Snakemake executor with the following:
```bash
pip install git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git
```

Currently, this executor requires that all input to the workflow is scoped to the current working directory. Therefore, you'll need to copy the
Snakefile and your input directory (as specified by `example_config.yaml`) to this directory:
```bash
cp ../../Snakefile . && \
cp -r ../../input .
```

Instead of editing `spras.sub` to define the workflow, this scenario requires editing the SPRAS profile in `spras_profile/config.yaml`. Make sure you specify the correct container, and change any other config values needed by your workflow (defaults are fine in most cases).

Then, to start the workflow with HTCondor in the CHTC pool, there are two options:

#### Snakemake From Your Own Terminal
The first option is to run Snakemake in a way that ties its execution to your terminal. This is good for testing short workflows and running short jobs. The downside is that closing your terminal causes the process to exit, removing any unfinished jobs. To use this option, invoke Snakemake directly by running:
```bash
snakemake --profile spras_profile
```

#### Long Running Snakemake Jobs (Managed by HTCondor)
The second option is to let HTCondor manage the Snakemake process, which allows the jobs to run as long as needed. Instead of seeing Snakemake output directly in your terminal, you'll be able to see it in a specified log file. To use this option, make sure `snakemake_long.py` is executable (you can run `chmod +x snakemake_long.py` from the AP to make sure it is), and then run:
```
./snakemake_long.py --profile spras_profile --htcondor-jobdir <path/to/logging/directory>
```

When run in this mode, all log files for the workflow will be placed into the path you provided for the logging directory. In particular, Snakemake's outputs with job progress can be found split between `<logdir>/snakemake-long.err` and `<logdir>/snakemake-long.out`. These will also log each rule and what HTCondor job ID was submitted for that rule (see the [troubleshooting section](#troubleshooting) for information on how to use these extra log files).

### Adjusting Resources

Resource requirements can be adjusted as needed in `spras_profile/config.yaml`, and HTCondor logs for this workflow can be found in `.snakemake/htcondor`.
You can set a different log directory by adding `htcondor-jobdir: /path/to/dir` to the profile's configuration.

To run this same workflow in the OSPool, add the following to the profile's default-resources block:
```
  classad_WantGlideIn: true
  requirements: |
    '(HAS_SINGULARITY == True) && (Poolname =!= "CHTC")'
```

**Note**: This workflow requires that the terminal session responsible for running snakemake stays active. Closing the terminal will suspend jobs,
but the workflow can use Snakemake's checkpointing to pick up any jobs where they left off.

**Note**: If you encounter an error that says `No module named 'spras'`, make sure you've `pip install`-ed the SPRAS module into your conda environment.

### Job Monitoring
To monitor the state of the job, you can use a second terminal to run `condor_q` for a snapshot of how the workflow is doing, or you can run `condor_watch_q` for realtime updates.

Upon completion, the `output` directory from the workflow should be returned as `spras/docker-wrappers/SPRAS/output`, along with several files containing the
workflow's logging information (anything that matches `logs/spras_*` and ending in `.out`, `.err`, or `.log`). If the job was unsuccessful, these files should
contain useful debugging clues about what may have gone wrong.

**Note**: If you want to run the workflow with a different version of SPRAS, or one that contains development updates you've made, rebuild this image against
the version of SPRAS you want to test, and push the image to your image repository. To use that container in the workflow, change the `container_image` line of
`spras.sub` to point to the new image.

### Troubleshooting
Some errors Snakemake might encounter while executing rules in the workflow boil down to bad luck in a distributed, heterogeneous computational environment, and it's expected that some errors can be solved simply by rerunning. If you encounter a Snakemake error, try restarting the workflow to see if the same error is generated in the same rule a second time -- repeatable, identical failures are more likely to indicate a more fundamental issue that might require user intervention to fix.

To investigate issues, start by referring to your logging directory. Each Snakemake rule submitted to HTCondor will log a corresponding HTCondor job ID in the Snakemake standard out/error. You can use this job ID to check the standard out, standard error, and HTCondor job log for that specific rule. In some cases the error will indicate a user-solvable issue, e.g. "input file not found" might point to a typo in some part of your workflow. In other cases, errors might be solved by retrying the workflow, which causes Snakemake to pick up where it left off.

If your workflow gets stuck on the same error after multiple consecutive retries and prevents your workflow from completing, this indicates some user/developer intervention is likely required. If you choose to open a github issue, please include a description of the error(s) and what troubleshooting steps you've already taken.

## Versions:

The versions of this image match the version of the spras package within it.
- v0.2.0: Add a header row to pathway output file format. Validate dataset label names. Streamline SPRAS image.
- v0.1.0: Created an image with SPRAS as an installed python module. This makes SPRAS runnable anywhere with Docker/Singularity. Note that the Snakefile should be
  runnable from any directory within the container.
