#######################
 Running with HTCondor
#######################

`HTCondor <https://htcondor.readthedocs.io/en/latest/>`_ is a
distributed workload management system that can be used to run computing
jobs on a cluster of machines, managing job submission, scheduling, and
execution across available compute resources.

This section describes how to run SPRAS workflows using HTCondor by
leveraging one of two different remote execution strategies:

-  Submitting all jobs in the workflow to a single remote Execution
   Point (EP), effectively moving the workflow to a single computer with
   all of the compute resources needed to run the workflow.

-  Using the Snakemake HTCondor executor to submit each job in the
   workflow to its own remote Execution Point (EP), thereby distributing
   the workflow across the cluster and allowing HTCondor to schedule and
   run jobs on available compute resources in parallel.

Either of these approaches may be desirable whenever you're running a
workflow with many compute-intensive or parallelizable steps, as
HTCondor can greatly accelerate the execution of such workflows.

The folder `htcondor/
<https://github.com/Reed-CompBio/spras/tree/main/htcondor>`_ inside the
SPRAS git repository contains several sets of files that can be used to
run SPRAS workflows in either of these remote execution modes.

Specifically, the set of files from the `htcondor/` directory needed for
the single-EP execution mode include:

-  ``spras.sub`` -- this is an HTCondor "submit file" that describes to
   HTCondor how to run SPRAS and what computing resources (e.g., CPUs,
   memory) your job needs to run successfully.

The files needed for the parallelized execution mode include:

-  ``spras_profile/config.yaml`` -- this is the Snakemake profile
   configuration file that tells Snakemake's HTCondor executor how to
   submit jobs and request resources (e.g., CPUs, memory).

-  ``snakemake_long.py`` -- this is a small integration script used to
   launch SPRAS with Snakemake on an HTCondor Access Point (AP).

-  ``spras.sh`` -- this is a small shell script needed during the
   parallelized execution of SPRAS jobs with HTCondor. While it's needed
   by the workflow, you likely won't have to interact with it.

These files are insufficient on their own to run SPRAS workflows in
either the single-EP or parallelized execution modes. For further
instructions, see `Submitting All Jobs to a Single EP`_ and `Submitting
Parallel Jobs`_ for additional instructions.

While you don't need to have prior HTCondor experience to follow along
with this guide, some experience may help you deal with complicated
issues that can arise when scaling up your computing pipelines.

*************************************************
 Creating Container Images for use with HTCondor
*************************************************

HTCondor's remote execution model typically requires that you ship the
full set of files and software dependencies needed to run your workflow
to the remote machine because it is assumed not to have anything
pre-installed, and EPs do not typically share a filesystem with the
machine from which you submit jobs (the AP). To work around this, you'll
need to create self-contained, portable execution environments
containing the dependencies SPRAS needs to run successfully. This is
best accomplished with Docker or Apptainer/Singularity container images.

Running SPRAS with HTCondor requires two sets of container images: one
that contains the SPRAS software, and one for each algorithm/PRM you
intend to run as part of your workflow.

There are two ways to obtain the appropriate container images:

#. Build them yourself using source files in the SPRAS repository (best
   if you require any non-released SPRAS software).
#. Pull pre-built images from Docker Hub (best if you plan to use a
   versioned SPRAS release).

Generally, you'll never have to build the images for individual
algorithms/PRMs yourself, as these are already available as pre-built
images on Docker Hub that you can pull and use in your workflows.
Because of this, instructions for building algorithm images from scratch
are not included here.

However, you may need to build the SPRAS container image yourself if you
want to run a non-released version of SPRAS that is not available as a
pre-built image on Docker Hub.

In either case, you'll still need to work with algorithm images from
Docker Hub, which can be browsed at
https://hub.docker.com/u/reedcompbio. If you know that all the images
you plan to work with are already hosted on Docker Hub, skip to
`Converting Docker Images to Apptainer/Singularity Images`_.

Building your Own SPRAS Image
=============================

There are a few prerequisites to building a SPRAS image from scratch:

#. Access to the ``docker`` CLI, which must be installed on the computer
   you'll use for building the image. While you could use another
   container technology that works with Dockerfiles, that is not covered
   here.

#. An account to a "container registry" (e.g., Docker Hub) where you can
   push your built images. This walkthrough assumes you'll use Docker
   Hub.

#. A cloned copy of SPRAS source code repository on the computer where
   you'll run ``docker`` commands.

These steps probably cannot be accomplished on your HTCondor Access
Point, because APs typically don't have the ``docker`` CLI installed.
Instead, you'll likely need to do this on a personal computer.

First, follow `Docker documentation
<https://docs.docker.com/engine/install/>`_ for installing Docker if it
isn't already installed.

Similarly, create a free account on `Dockerhub
<https://hub.docker.com/>`_.

Finally, clone the SPRAS repository on your local machine (assumes you
already have ``git`` installed):

.. code:: bash

   $ git clone https://github.com/Reed-CompBio/spras.git

If you need to work with a specific branch or your own fork of SPRAS,
adjust this command accordingly.

Next, follow the instructions located `here
<https://github.com/Reed-CompBio/spras/tree/main/docker-wrappers/SPRAS>`_
for building the image. In summary, this will typically entail running
the following commands from a terminal:

.. code:: bash

   $ cd spras/
   $ DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t <your_dockerhub_username>/spras:<some-version-tag> -f docker-wrappers/SPRAS/Dockerfile .

When your build is complete, push it to the Docker Hub registry:

.. code:: bash

   $ docker push <your_dockerhub_username>/spras:<some-version-tag>

Working with a Released SPRAS Image
===================================

If you plan to work with a tagged version of SPRAS, you do not need to
follow the instructions for building from source. Instead, you'll need
to identify the appropriate Docker image URL from Docker Hub, e.g. the
URL ``docker://reedcompbio/spras:0.6.0`` corresponds to the ``0.6.0``
release of SPRAS.

You can browse available versions on `Docker Hub
<https://hub.docker.com/r/reedcompbio/spras/tags>`_. Generally you
should try to use the latest/newest release whenever possible.

Converting Docker Images to Apptainer/Singularity Images
========================================================

The last image-related step you need to take for running SPRAS with
HTCondor is to convert your relevant Docker images to
Apptainer/Singularity images. This section assumes all the images you
need are already available via Docker Hub. If that's not the case,
return to `Building your Own SPRAS Image
<#building-your-own-spras-image>`_.

`Apptainer <https://apptainer.org/>`_, formerly known as Singularity, is
another container image format designed to work with distributed
computing applications like HTCondor. In particular, Apptainer lets you
create ``.sif`` files representing the entire image that can be shipped
with an HTCondor job for automatic setup.

This step can typically be completed via your HTCondor Access Point, but
your HTCondor pool may have its own specific instructions for how to
create Apptainer images.

Assuming you have Apptainer installed, you can build a ``.sif`` image
from any Docker URL using the following recipe:

.. code:: bash

   $ apptainer build <new image name>.sif docker://<name of container on DockerHub>

For example, creating an Apptainer image for the ``0.6.0`` SPRAS image
might look like:

.. code:: bash

   $ apptainer build spras-0.6.0.sif docker://reedcompbio/spras:0.6.0

Creating a ``.sif`` image for the ``allpairs`` image from Dockerhub
might look like:

.. code:: bash

   $ apptainer build allpairs_v4.sif docker://reedcompbio/allpairs:v4

After running these commands, new files called ``spras-0.6.0.sif`` and
``allpairs_v4.sif`` will exist in the directory where the command was
run. Note that the Docker image for SPRAS ``0.6.0`` does not use a ``v``
in the tag name.

Note that it is important you use the ``.sif`` extension with these
files.

******************************************************
 Preparing to Run SPRAS on your HTCondor Access Point
******************************************************

Submitting work to an HTCondor cluster requires access to an Access
Point (AP) for that cluster. This section assumes you already have
access to an HTCondor AP and know how to log into it.

Once you're logged into the AP, you'll first want to clone the SPRAS
repository:

.. code:: bash

   $ git clone https://github.com/Reed-CompBio/spras.git

It's also crucial that you work with the repository checked out to the
version of SPRAS corresponding to the container images you plan to use.
For example, if you identified that you need the ``0.6.0`` release of
SPRAS, you should check out the repository to the corresponding tag:

.. code:: bash

   $ cd spras
   $ git checkout 0.6.0

.. danger::

   Unless you're building your own SPRAS image from the repository's
   main branch using the instructions outlined in `Building your Own
   SPRAS Image <#building-your-own-spras-image>`_, you should always
   checkout a specific git tag. Failure to do so may result in
   difficult-to-diagnose, cryptic incompatibilities between the
   repository and the container images.

.. warning::

   It's possible that the version of SPRAS you check out is incompatible
   with some instructions in this page. This is the case whenever your
   checked out tag does not contain a top-level ``htcondor/`` directory.
   If that's the case, look for HTCondor instructions in the
   ``docker-wrappers/SPRAS`` directory. However, this is typically a
   sign you should use a more recent SPRAS version, as older versions
   will have significant drawbacks when working with HTCondor.

************************************
 Submitting All Jobs to a Single EP
************************************

Running all SPRAS steps on a single remote Execution Point (EP) is a
good way to get started with HTCondor, but it is significantly less
efficient than using HTCondor's distributed capabilities. This approach
is best suited for workflows that are not computationally intensive, or
for testing and debugging purposes.

Before submitting all SPRAS jobs to a single remote Execution Point
(EP), you'll need to set up three things:

#. You'll need to modify ``htcondor/spras.sub``, this workflow's "submit
   file", with details about images and computing resources needed to
   run the job:

   #. First, declare your container images. The SPRAS image is declared
      via the submit file's ``container_image`` key, e.g.:

      ..
         technically NOT bash, but there's no type for submit files...

      .. code:: bash

         # Tell the job to start in the execution environment defined
         # by the SPRAS image. This path is relative to the directory
         # from which you submit the job.
         container_image = spras-0.6.0.sif

      All other algorithm containers should be declared via the
      ``PRM_IMAGES`` key, e.g.:

      .. code:: bash

         # These paths are relative to the directory from which you
         # submit the job.
         PRM_IMAGES = allpairs_v4.sif, meo_v2.sif

   #. Adjust the submit file's resource requests to match what you
      expect your job will need in terms of CPU, memory, and disk
      requirements. Note that the request for disk must be sufficient to
      fit your workflow's inputs, any container images shipped with the
      job, and the workflow's outputs. If you need help estimating these
      values, ask the SPRAS group for guidance.

   #. Double check other values in the submit file for various features
      you may wish to use, such as submission to the Open Science Pool
      (OSPool) or specifying a different logging directory than the one
      filled in by default.

   .. tip::

      all paths in the submit file are relative to the directory from
      which you run ``condor_submit``, which should be the root of the
      SPRAS repository.

#. You'll need to ensure your SPRAS configuration file has a few key
   values set, including ``unpack_singularity: true`` and
   ``containers.framework: apptainer``. Additionally, any algorithm/PRM
   images should be declared using the appropriate image overrides in
   your config file such that they point to your ``.sif`` images. For
   example, a ``containers`` configuration for running ``allpairs``
   might look like:

   .. code:: yaml

      containers:
        registry:
          base_url: docker.io
          owner: reedcompbio

        framework: apptainer
        unpack_singularity: true

        images:
          # assumes the .sif is located at spras/allpairs_v4.sif
          allpairs: "allpairs_v4.sif"

#. Finally, it's best practice to create the logging directory
   configured in the submit file before submitting the job, e.g. to
   create the default log directory, run ``mkdir htcondor/logs`` from
   the root of the repository.

Once these steps are complete, you can submit the job from the root of
the SPRAS repository by running ``condor_submit htcondor/spras.sub``.

See `Job Monitoring`_ for instructions on monitoring the workflow while
it runs.

When the job completes, the ``output/`` directory from the workflow
should be returned locally as ``output/``.

**************************
 Submitting Parallel Jobs
**************************

Parallelizing SPRAS workflows with HTCondor requires much of the same
setup as the previous section, but with several additions.

#. Build/activate the SPRAS conda/mamba environment and ``pip install``
   the SPRAS module (via ``pip install .`` inside the SPRAS directory).

#. Install the `HTCondor Snakemake executor
   <https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__;
   once your SPRAS conda/mamba environment is activated and SPRAS is
   ``pip install``-ed, you can install the HTCondor Snakemake executor
   with the following:

   .. code:: bash

      $ pip install snakemake-executor-plugin-htcondor

#. Instead of editing ``spras.sub`` to define the workflow, this
   scenario requires editing the SPRAS profile in
   ``htcondor/spras_profile/config.yaml``. Make sure you specify the
   correct SPRAS image and computing resource requirements. However,
   unlike the single-EP workflow, the container image overrides don't
   need to be explicitly encoded here. Rather, it should suffice to
   declare them as image overrides in your SPRAS config yaml.

#. Modify your SPRAS configuration file to set ``unpack_singularity:
   true`` and ``containers.framework: apptainer``. Additionally, any
   algorithm/PRM images should be declared using the appropriate image
   overrides in your config file such that they point to your ``.sif``
   images. For example, a ``containers`` configuration for running
   ``allpairs`` might look like:

   .. code:: yaml

      containers:
        registry:
          base_url: docker.io
          owner: reedcompbio

        framework: apptainer
        unpack_singularity: true

        images:
          # assumes the .sif is located at spras/allpairs_v4.sif
          allpairs: "allpairs_v4.sif"

Then, to start the workflow with HTCondor in the CHTC pool, there are
two options:

HTCondor-Managed Snakemake Jobs (Recommended)
=============================================

The first option is to let HTCondor manage the Snakemake process, which
allows the jobs to run as long as needed. Instead of seeing Snakemake
output directly in your terminal, you'll be able to see it in a
specified log file. To use this option, run from the repository root:

.. code:: bash

   $ ./htcondor/snakemake_long.py --profile htcondor/spras_profile/

A convenience script called ``run_htcondor.sh`` is also provided in the
repository root. You can execute this script by running:

.. code:: bash

   $ ./run_htcondor.sh

When executed in this mode, all log files for the workflow will be
placed into the logging directory (``htcondor/logs`` by default). In
particular, Snakemake's stdout/stderr outputs containing your workflow's
progress can be found split between ``htcondor/logs/snakemake.err`` and
``htcondor/logs/snakemake.out``. These will also log each rule and what
HTCondor job ID was submitted for that rule (see the `troubleshooting
section <#troubleshooting>`__ for information on how to use these extra
log files).

.. tip::

   While you're in the initial stages of developing/debugging your
   workflow, it's very useful to invoke Snakemake with the ``--verbose``
   flag. This can be passed to Snakemake via the ``snakemake_long.py``
   script by adding it to the script's argument list, e.g.:

.. code:: bash

   ./htcondor/snakemake_long.py --profile htcondor/spras_profile/ --verbose

If you use mamba instead of conda for environment management, you can
specify this with the ``--env-manager`` flag:

.. code:: bash

   ./htcondor/snakemake_long.py --profile htcondor/spras_profile/ --env-manager mamba

Snakemake From Your Own Terminal (Not Recommended)
==================================================

The second option is to run Snakemake in a way that ties its execution
to your terminal. This is good for testing short workflows and running
short jobs. The downside is that closing your terminal causes the
process to exit, removing any unfinished jobs. To use this option,
invoke Snakemake directly from the repository root by running:

.. code:: bash

   $ snakemake --profile htcondor/spras_profile/

.. tip::

   Running the workflow in this way requires that your terminal session
   stays active. Closing the terminal will suspend ongoing jobs, but
   Snakemake will handle picking up where any previously-completed jobs
   left off when you restart the workflow.

Adjusting Resources
===================

Resource requirements can be adjusted as needed in
``htcondor/spras_profile/config.yaml``, and HTCondor logs for this
workflow can be found in your log directory. You can set a different log
directory by changing the configured ``htcondor-jobdir`` in the
profile's configuration. Alternatively, you can pass a different log
directory when invoking Snakemake with the ``--htcondor-jobdir``
argument.

To run this same workflow in the OSPool, add the following to the
profile's default-resources block:

.. code::

   classad_WantGlideIn: true
   requirements: |
     '(HAS_SINGULARITY == True) && (Poolname =!= "CHTC")'

.. tip::

   If you encounter an error that says ``No module named 'spras'``, make
   sure you've ``pip install``-ed the SPRAS module into your conda
   environment.

****************
 Job Monitoring
****************

To monitor the state of the job, you can use a second terminal to run
``condor_q`` for a snapshot of how the workflow is doing, or you can run
``condor_watch_q`` for realtime updates.

Upon completion, the ``output/`` directory from the workflow should be
returned as ``output/`` in the repo root, along with several files
containing the workflow's logging information (anything that matches
``htcondor/logs/spras_*`` and ending in ``.out``, ``.err``, or
``.log``). If the job was unsuccessful, these files should contain
useful debugging clues about what may have gone wrong.

*****************
 Troubleshooting
*****************

Some errors Snakemake might encounter while executing rules in the
workflow boil down to bad luck in a distributed, heterogeneous
computational environment, and it's expected that some errors can be
solved simply by rerunning. If you encounter a Snakemake error, try
restarting the workflow to see if the same error is generated in the
same rule a second time -- repeatable, identical failures are more
likely to indicate a more fundamental issue that might require user
intervention to fix.

To investigate issues, start by referring to your logging directory.
Each Snakemake rule submitted to HTCondor will log a corresponding
HTCondor job ID in the Snakemake standard out/error. You can use this
job ID to check the standard out, standard error, and HTCondor job log
for that specific rule. In some cases the error will indicate a
user-solvable issue, e.g. "input file not found" might point to a typo
in some part of your workflow. In other cases, errors might be solved by
retrying the workflow, which causes Snakemake to pick up where it left
off.

If your workflow gets stuck on the same error after multiple consecutive
retries and prevents your workflow from completing, this indicates some
user/developer intervention is likely required. If you choose to open a
github issue, please include a description of the error(s) and what
troubleshooting steps you've already taken.

How To Fix HTCondor Creds Error
===============================

If you attempt to run a SPRAS HTCondor workflow and encounter an error
containing:

.. code::

   raise CredsError("Credentials not found for this workflow")

it indicates you must upgrade the version of the HTCondor Snakemake
executor bundled with your conda environment.

To upgrade, from your activated ``spras`` conda environment run:

.. code:: bash

   pip install --force-reinstall git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git

Subsequently, verify that the git sha of the installed version matches
the latest commit sha from the repo:

.. code:: bash

   pip freeze | grep snakemake-executor-plugin-htcondor

This should result in something like:

.. code::

   snakemake-executor-plugin-htcondor @ git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git@68a345f8b9a281d8188fc33f134190c9f4ef7f27

where the trailing hexadecimal (everything after ``@``) indicates the
commit. You can find the latest upstream commit by visiting `the
executor repository
<https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__ and
inspecting the commit history.

If the preceding steps did not update the installed version, you may
need to delete and rebuild your ``spras`` conda environment.
