#######################
 Running with HTCondor
#######################

The folder `htcondor/
<https://github.com/Reed-CompBio/spras/tree/main/htcondor>`_ inside the
SPRAS git repository contains several files that can be used to run
workflows with this container on HTCondor. To use the ``spras`` image in
this environment, first login to an HTCondor Access Point (AP). Then,
from the AP clone this repo:

.. code:: bash

   git clone https://github.com/Reed-CompBio/spras.git

.. tip::

   To work with SPRAS in HTCondor, it is recommended that you build an
   Apptainer image instead of using Docker. See `Converting Docker
   Images to Apptainer/Singularity Images`_ for instructions.
   Importantly, the Apptainer image must be built for the linux/amd64
   architecture. Most HTCondor APs will have ``apptainer`` installed,
   but they may not have ``docker``. If this is the case, you can build
   the image with Docker on your local machine, push the image to Docker
   Hub, and then convert it to Apptainer's ``sif`` format on the AP.

.. important::

   **Keep your local SPRAS repo and your container image on the same
   version.** When the workflow runs, Snakemake uses the ``Snakefile``
   from your local repo checkout during remote execution -- *not* the
   one baked into the container image. The rest of the SPRAS code,
   however, comes from the container. If the ``Snakefile`` on your
   current branch expects a version of the SPRAS package that the
   container doesn't provide, you get difficult-to-diagnose failures at
   runtime, commonly a ``ModuleNotFoundError`` or other import/attribute
   errors deep in a job's logs.

   There are two reliable ways to keep the repo and the container in
   sync. Pick whichever fits your situation:

   #. **Build the container to match your repo.** If you are developing
      against a specific branch or have local changes, rebuild the SPRAS
      image from that exact code (see `Converting Docker Images to
      Apptainer/Singularity Images`_), push it to Docker Hub if needed,
      and submit your jobs using that image. This guarantees the
      container holds the same SPRAS version as your ``Snakefile``.

   #. **Check out the repo to match the container.** If you want to use
      a published image such as ``reedcompbio/spras:0.6.0``, check out
      the matching release of the repository so your ``Snakefile`` lines
      up with it:

      .. code:: bash

         git checkout 0.6.0

   Either way, the goal is the same: the ``Snakefile`` in your checkout
   and the SPRAS code inside the container must come from the same
   version.

There are currently two options for running SPRAS with HTCondor. The
first is to submit all SPRAS jobs to a single remote Execution Point
(EP). The second is to use the Snakemake HTCondor executor to
parallelize the workflow by submitting each job to its own EP.

***********************************
 Which Files Are Used in Each Mode
***********************************

The ``htcondor`` directory contains several files, but not all of them
are used in both run modes. A common point of confusion is which files
apply where -- for example, ``spras.sub`` is only used when submitting
to a single EP and is ignored when running in parallel. The table below
summarizes what each file is for and which mode uses it, so you know
what to edit before submitting.

.. list-table::
   :header-rows: 1
   :widths: 34 13 13 40

   -  -  File
      -  Single EP
      -  Parallel
      -  Purpose

   -  -  ``htcondor/spras.sub``
      -  ✓
      -
      -  HTCondor submit file that runs the entire workflow as a single
         job on one EP.

   -  -  ``htcondor/spras.sh``
      -  ✓
      -  ✓
      -  Wrapper script that invokes Snakemake inside the container.
         Used as the executable in both modes.

   -  -  ``htcondor/spras_profile/config.yaml``
      -
      -  ✓
      -  Snakemake HTCondor-executor profile defining resources and
         submission settings for parallel runs.

   -  -  ``htcondor/snakemake_long.py``
      -
      -  ✓
      -  Launches Snakemake as a long-running managed job so the
         workflow survives terminal disconnects.

   -  -  ``run_htcondor.sh``
      -
      -  ✓
      -  Convenience wrapper (in the repository root) around
         ``snakemake_long.py``.

**********************************************************
 Converting Docker Images to Apptainer/Singularity Images
**********************************************************

It may be necessary in some cases to create an Apptainer image for
SPRAS, especially if you intend to run your workflow using distributed
systems like HTCondor. Apptainer (formerly known as Singularity) uses
image files with ``.sif`` extensions. Assuming you have Apptainer
installed, you can create your own sif image from an already-built
Docker image with the following command:

.. code:: bash

   apptainer build <new image name>.sif docker://<name of container on DockerHub>

For example, creating an Apptainer image for the ``v0.6.0`` SPRAS image
might look like:

.. code:: bash

   apptainer build spras-v0.6.0.sif docker://reedcompbio/spras:0.6.0

After running this command, a new file called ``spras-v0.6.0.sif`` will
exist in the directory where the command was run. Note that the Docker
image does not use a "v" in the tag.

.. warning::

   Do not run ``apptainer build`` (or otherwise pull/convert large
   images) directly on an Access Point. APs are shared, login-style
   nodes, and image builds are resource-intensive enough that doing so
   is discouraged and may violate your pool's usage policies. Instead,
   build images inside an interactive job on an Execution Point. If
   you're working at CHTC, follow their guide for building Apptainer
   images in an interactive job:
   https://chtc.cs.wisc.edu/uw-research-computing/apptainer-htc.html
   Specifically, create the apptainer.sub file on the AP and run
   ``condor_submit -i apptainer.sub`` on the AP.

   The ``apptainer build`` commands shown above and in the next section
   are meant to be run from within such an interactive job (or on your
   local machine), not on the AP itself.

*********************************************
 Pre-Building Per-Algorithm Container Images
*********************************************

In addition to the SPRAS runtime image (the container that runs
Snakemake itself), each pathway reconstruction method runs inside its
own container -- ``pathlinker``, ``omicsintegrator1``, ``mincostflow``,
and so on. By default, these per-algorithm images are pulled from a
registry (Docker Hub) at runtime, *on the Execution Point (EP) where
each job lands*.

We **strongly** recommend that you instead pre-build these images once,
up front, and reference them from your config file. There are two
reasons this matters in an HTCondor environment:

#. **It avoids redundant work.** When images are pulled at runtime,
   every job that uses a given algorithm re-pulls (and, under
   ``singularity``/``apptainer``, re-converts and re-unpacks) the same
   image. In a parallelized workflow that can mean hundreds of EPs each
   repeating the same build. Building each image once up front and
   letting HTCondor transfer the finished ``.sif`` file to each EP turns
   that repeated work into a one-time cost.

#. **It avoids Docker Hub rate limiting.** A distributed workflow can
   issue a large number of near-simultaneous pulls from Docker Hub from
   many different EPs. This routinely trips Docker Hub's anonymous
   pull-rate limits, which surfaces as hard-to-diagnose, intermittent
   runtime failures. Transferring a pre-built image sidesteps the
   registry entirely at job time.

How To Pre-Build and Reference Images
=====================================

#. From the root of the SPRAS repository, create a folder to hold your
   pre-built images:

   .. code:: bash

      mkdir images

#. Build an Apptainer ``.sif`` image for each algorithm you intend to
   run, placing each one in ``images/``. As with the SPRAS runtime
   image, these must be built for the ``linux/amd64`` architecture, and
   -- as noted in the warning above -- the ``apptainer build`` commands
   below should be run from within an interactive build job (or on your
   local machine), **not** directly on the Access Point. For example, to
   pre-build the Omics Integrator 1 and PathLinker images:

   .. code:: bash

      apptainer build images/omics-integrator-1_v2.sif docker://reedcompbio/omics-integrator-1:v2
      apptainer build images/pathlinker_v2.sif docker://reedcompbio/pathlinker:v2

#. In your SPRAS configuration file, point each algorithm at its
   pre-built image using the ``containers.images`` block. Keys are
   algorithm names (matching the ``algorithms`` list in the same config
   file), and values are the paths to the ``.sif`` files:

   .. code:: yaml

      containers:
        framework: singularity
        unpack_singularity: true
        images:
          omicsintegrator1: "images/omics-integrator-1_v2.sif"
          pathlinker: "images/pathlinker_v2.sif"
      ...
      Algorithms:
        - name: "pathlinker"
          include: true
          ...
        - name: "omicsintegrator1"
          include: true
          ...

   Any algorithm that is *not* listed here falls back to pulling its
   image from the registry at runtime, so list every algorithm you want
   to run.

.. important::

   All image paths in the config file are relative to the location you
   submit from -- which, in these instructions, is the root of the SPRAS
   repository. Using a repository-rooted ``images/`` folder (as above)
   keeps these paths stable regardless of which run mode you use. Avoid
   absolute paths, since the EP that runs a job will not share a
   filesystem with the AP.

.. note::

   Local ``.sif`` overrides are only supported when the container
   framework is set to ``singularity``/``apptainer``. If the framework
   is Docker, ``.sif`` entries are ignored with a warning. See the
   ``containers`` section of ``config/config.yaml`` for the full set of
   accepted value formats (bare image names, full registry references,
   and local ``.sif`` paths).

How the Images Reach the EP
===========================

The way your pre-built images get to the EP depends on which run mode
you use:

-  **Parallel jobs** (``shared-fs-usage: none`` in
   ``htcondor/spras_profile/config.yaml``): any ``.sif`` path listed in
   ``containers.images`` is automatically added to that job's
   ``htcondor_transfer_input_files``, so the HTCondor executor transfers
   the image to the EP alongside the rest of the job's inputs. No
   further action is required.

-  **Single EP**: the entire workflow runs as one job defined by
   ``htcondor/spras.sub``, so you must transfer the ``images/`` folder
   yourself by adding it to that file's ``transfer_input_files`` line,
   e.g.:

   .. code::

      transfer_input_files = $(CONFIG_FILE), $(INPUT_DIR), $(SNAKEFILE), images

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

#. You'll need to modify ``htcondor/spras.sub`` to point at your general
   spras container image (built from ``docker-wrappers/SPRAS``), along
   with any other configuration changes you want to make like choosing a
   logging directory or toggling OSPool submission. Note that all paths
   in the submit file are relative to the directory from which you run
   ``condor_submit``, which will typically be the root of the SPRAS
   repository.

   .. note::

      OSPool submission is disabled by default. To enable it, uncomment
      the relevant lines near the bottom of ``htcondor/spras.sub`` --
      the in-file comments there explain exactly which lines to
      uncomment and when each is needed.

#. You'll need to ensure your SPRAS configuration file has a few key
   values set, including ``unpack_singularity: true`` and
   ``containers.framework: singularity``.

#. Finally, it's best practice to create the logging directory
   configured in the submit file before submitting the job, e.g. to
   create the default log directory, run ``mkdir htcondor/logs`` from
   the root of the repository.

Once these steps are complete, you can submit the job from the root of
the SPRAS repository by running ``condor_submit htcondor/spras.sub``.

When the job completes, the ``output`` directory from the workflow
should be returned as ``output``.

**************************
 Submitting Parallel Jobs
**************************

Parallelizing SPRAS workflows with HTCondor requires much of the same
setup as the previous section, but with two additions.

#. :ref:`Build/activate the SPRAS conda/mamba environment
   <using-a-conda-environment>` and ``pip install`` the SPRAS module
   (via ``pip install .`` inside the SPRAS directory).

#. Install the `HTCondor Snakemake executor
   <https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__;
   once your SPRAS conda/mamba environment is activated and SPRAS is
   ``pip install``-ed, you can install the HTCondor Snakemake executor
   with the following:

   .. code:: bash

      pip install snakemake-executor-plugin-htcondor

#. Instead of editing ``spras.sub`` to define the workflow, this
   scenario requires editing the SPRAS profile in
   ``htcondor/spras_profile/config.yaml``. Make sure you specify the
   correct SPRAS container image, and change any other config values
   needed by your workflow (defaults are fine in most cases). Memory and
   hardware requirements are also set here. To use a config file other
   than ``config/config.yaml``, set the path next to the ``configfile:``
   variable in this file.

   .. note::

      Despite the shared file name,
      ``htcondor/spras_profile/config.yaml`` is **not** the same as your
      SPRAS config file (typically ``config/config.yaml``), and they
      serve different purposes:

      -  ``htcondor/spras_profile/config.yaml`` is a *Snakemake
         profile*. It controls *how* Snakemake runs the workflow on
         HTCondor -- the executor, per-job resources (memory, disk,
         CPUs), the container image, and so on.

      -  ``config/config.yaml`` is the *SPRAS config file*. It defines
         *what* the workflow does -- the algorithms, datasets, and
         analysis options.

      The two are linked by the ``configfile:`` key in the profile,
      which tells Snakemake which SPRAS config file to load. So when
      these instructions mention editing "the SPRAS profile" versus
      "your SPRAS config file," they are referring to these two
      different files -- double-check you're editing the intended one.

#. Modify your SPRAS configuration file to set ``unpack_singularity:
   true`` and ``containers.framework: singularity``.

Then, to start the workflow with HTCondor in the CHTC pool, there are
two options:

Snakemake From Your Own Terminal
================================

The first option is to run Snakemake in a way that ties its execution to
your terminal. This is good for testing short workflows and running
short jobs. The downside is that closing your terminal causes the
process to exit, removing any unfinished jobs. To use this option,
invoke Snakemake directly from the repository root by running:

.. code:: bash

   snakemake --profile htcondor/spras_profile/

.. tip::

   Running the workflow in this way requires that your terminal session
   stays active. Closing the terminal will suspend ongoing jobs, but
   Snakemake will handle picking up where any previously-completed jobs
   left off when you restart the workflow.

Long Running Snakemake Jobs (Managed by HTCondor)
=================================================

The second option is to let HTCondor manage the Snakemake process, which
allows the jobs to run as long as needed. Instead of seeing Snakemake
output directly in your terminal, you'll be able to see it in a
specified log file. To use this option, run from the repository root:

.. code:: bash

   ./htcondor/snakemake_long.py --profile htcondor/spras_profile/

A convenience script called ``run_htcondor.sh`` is also provided in the
repository root. You can execute this script by running:

.. code:: bash

   ./run_htcondor.sh

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

*********************
 Adjusting Resources
*********************

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

Upon completion, the ``output`` directory from the workflow should be
returned as ``output``, along with several files containing the
workflow's logging information (anything that matches
``htcondor/logs/spras_*`` and ending in ``.out``, ``.err``, or
``.log``). If the job was unsuccessful, these files should contain
useful debugging clues about what may have gone wrong.

.. tip::

   If you want to run the workflow with a different version of SPRAS, or
   one that contains development updates you've made, rebuild this image
   against the version of SPRAS you want to test, and push the image to
   your image repository. To use that container in the workflow, change
   the ``container_image`` line of ``spras.sub`` to point to the new
   image.

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

How To Fix a Locked Working Directory
=====================================

While a workflow runs, Snakemake places a lock on its working directory
so that two runs can't modify the same outputs at once. Normally
Snakemake releases this lock when it finishes or is stopped cleanly. If
a run is interrupted abruptly, however, the lock can be left behind --
the most common cause is removing a running workflow with ``condor_rm``
(which kills the managed Snakemake job before it can clean up), but
killing a terminal-attached run before it exits will do the same.

The next time you launch the workflow, Snakemake refuses to start and
raises a ``LockException``, reporting that the directory cannot be
locked. This is easy to miss in the long-running (HTCondor-managed)
mode, because the error is written to your log directory (e.g.
``htcondor/logs/snakemake.err``) instead of your terminal -- so the
submitted job can look like it finished immediately even though no
workflow steps ever ran.

To clear a stale lock, run Snakemake once with the ``--unlock`` flag,
using the same profile you launch the workflow with, from the root of
the SPRAS repository:

.. code:: bash

   snakemake --profile htcondor/spras_profile/ --unlock

This only removes the lock; it does not run any workflow steps. Once it
completes, re-launch the workflow as usual and Snakemake will pick up
where it left off.

.. warning::

   Only unlock when you're certain no other Snakemake process is still
   running against the same directory. The lock exists to prevent
   concurrent runs from corrupting each other's state, so unlocking
   while a real run is in progress can lead to inconsistent output.

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
