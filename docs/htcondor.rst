Running with HTCondor
=====================

The folder `docker-wrappers/SPRAS <https://github.com/Reed-CompBio/spras/tree/main/docker-wrappers/SPRAS>`_
inside the SPRAS git repository contains several files that can be used to
run workflows with this container on HTCondor. To use the ``spras``
image in this environment, first login to an HTCondor Access Point (AP).
Then, from the AP clone this repo:

.. code:: bash

   git clone https://github.com/Reed-CompBio/spras.git

**Note:** To work with SPRAS in HTCondor, it is recommended that you
build an Apptainer image instead of using Docker. See
`Converting Docker Images to Apptainer/Singularity Images`_ for
instructions. Importantly, the Apptainer image must be built for the
linux/amd64 architecture. Most HTCondor APs will have ``apptainer``
installed, but they may not have ``docker``. If this is the case, you
can build the image with Docker on your local machine, push the image to
Docker Hub, and then convert it to Apptainer's ``sif`` format on the AP.

**Note:** It is best practice to make sure that the Snakefile you copy
for your workflow is the same version as the Snakefile baked into your
workflow's container image. When this workflow runs, the Snakefile you
just copied will be used during remote execution instead of the
Snakefile from the container. As a result, difficult-to-diagnose
versioning issues may occur if the version of SPRAS in the remote
container doesn't support the Snakefile on your current branch. The
safest bet is always to create your own image so you always know what's
inside of it.

There are currently two options for running SPRAS with HTCondor. The
first is to submit all SPRAS jobs to a single remote Execution Point
(EP). The second is to use the Snakemake HTCondor executor to
parallelize the workflow by submitting each job to its own EP.

Converting Docker Images to Apptainer/Singularity Images
--------------------------------------------------------

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

Submitting All Jobs to a Single EP
----------------------------------

Navigate to the ``spras/docker-wrappers/SPRAS`` directory and create the
``logs/`` directory (``mkdir logs``). Next, modify ``spras.sub`` so that
it uses the SPRAS apptainer image you created:

::

   container_image = < your spras image >.sif

Make sure to modify the configuration file to have
``unpack_singularity`` set to ``true``, and ``containers.framework`` set
to ``singularity``: else, the workflow will (likely) fail.

Then run ``condor_submit spras.sub``, which will submit SPRAS to
HTCondor as a single job with as many cores as indicated by the
``NUM_PROCS`` line in ``spras.sub``, using the value of
``EXAMPLE_CONFIG`` as the SPRAS configuration file. By default, the
``example_config.yaml`` runs everything except for ``cytoscape``, which
appears to fail periodically in HTCondor.

**Note**: The ``spras.sub`` submit file is an example of how this
workflow could be submitted from a CHTC Access Point (AP) to the OSPool.
To run in the local CHTC pool, omit the ``+WantGlideIn`` and
``requirements`` lines.

Submitting Parallel Jobs
------------------------

Parallelizing SPRAS workflows with HTCondor requires the same setup as
the previous section, but with two additions. First, it requires an
activated SPRAS pixi environment with a ``pip install``-ed version of
the SPRAS module (via ``pip install .`` inside the SPRAS directory).

Second, it requires an experimental executor for HTCondor that has been
forked from the upstream `HTCondor Snakemake
executor <https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__.

After activating your ``spras`` pixi environment and ``pip``-installing
SPRAS, you can install the HTCondor Snakemake executor with the
following:

.. code:: bash

   pip install git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git

Currently, this executor requires that all input to the workflow is
scoped to the current working directory. Therefore, you'll need to copy
the Snakefile and your input directory (as specified by
``example_config.yaml``) to this directory:

.. code:: bash

   cp ../../Snakefile . && \
   cp -r ../../input .

Instead of editing ``spras.sub`` to define the workflow, this scenario
requires editing the SPRAS profile in ``spras_profile/config.yaml``.
Make sure you specify the correct container, and change any other config
values needed by your workflow (defaults are fine in most cases).

Then, to start the workflow with HTCondor in the CHTC pool, there are
two options:

Snakemake From Your Own Terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first option is to run Snakemake in a way that ties its execution to
your terminal. This is good for testing short workflows and running
short jobs. The downside is that closing your terminal causes the
process to exit, removing any unfinished jobs. To use this option,
invoke Snakemake directly by running:

.. code:: bash

   snakemake --profile spras_profile

Long Running Snakemake Jobs (Managed by HTCondor)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The second option is to let HTCondor manage the Snakemake process, which
allows the jobs to run as long as needed. Instead of seeing Snakemake
output directly in your terminal, you'll be able to see it in a
specified log file. To use this option, make sure ``snakemake_long.py``
is executable (you can run ``chmod +x snakemake_long.py`` from the AP to
make sure it is), and then run:

::

   ./snakemake_long.py --profile spras_profile --htcondor-jobdir <path/to/logging/directory>

When run in this mode, all log files for the workflow will be placed
into the path you provided for the logging directory. In particular,
Snakemake's outputs with job progress can be found split between
``<logdir>/snakemake-long.err`` and ``<logdir>/snakemake-long.out``.
These will also log each rule and what HTCondor job ID was submitted for
that rule (see the `troubleshooting section <#troubleshooting>`__ for
information on how to use these extra log files).

Adjusting Resources
-------------------

Resource requirements can be adjusted as needed in
``spras_profile/config.yaml``, and HTCondor logs for this workflow can
be found in ``.snakemake/htcondor``. You can set a different log
directory by adding ``htcondor-jobdir: /path/to/dir`` to the profile's
configuration.

To run this same workflow in the OSPool, add the following to the
profile's default-resources block:

::

     classad_WantGlideIn: true
     requirements: |
       '(HAS_SINGULARITY == True) && (Poolname =!= "CHTC")'

**Note**: This workflow requires that the terminal session responsible
for running snakemake stays active. Closing the terminal will suspend
jobs, but the workflow can use Snakemake's checkpointing to pick up any
jobs where they left off.

**Note**: If you encounter an error that says
``No module named 'spras'``, make sure you've ``pip install``-ed the
SPRAS module into your pixi environment.

Job Monitoring
--------------

To monitor the state of the job, you can use a second terminal to run
``condor_q`` for a snapshot of how the workflow is doing, or you can run
``condor_watch_q`` for realtime updates.

Upon completion, the ``output`` directory from the workflow should be
returned as ``spras/docker-wrappers/SPRAS/output``, along with several
files containing the workflow's logging information (anything that
matches ``logs/spras_*`` and ending in ``.out``, ``.err``, or ``.log``).
If the job was unsuccessful, these files should contain useful debugging
clues about what may have gone wrong.

**Note**: If you want to run the workflow with a different version of
SPRAS, or one that contains development updates you've made, rebuild
this image against the version of SPRAS you want to test, and push the
image to your image repository. To use that container in the workflow,
change the ``container_image`` line of ``spras.sub`` to point to the new
image.

Troubleshooting
---------------

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you attempt to run a SPRAS HTCondor workflow and encounter an error
containing:

::

   raise CredsError("Credentials not found for this workflow")

it indicates you must upgrade the version of the HTCondor Snakemake
executor bundled with your pixi environment.

To upgrade, from your activated ``spras`` pixi environment run:

.. code:: bash

   pip install --force-reinstall git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git

Subsequently, verify that the git sha of the installed version matches
the latest commit sha from the repo:

.. code:: bash

   pip freeze | grep snakemake-executor-plugin-htcondor

This should result in something like:

::

   snakemake-executor-plugin-htcondor @ git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git@68a345f8b9a281d8188fc33f134190c9f4ef7f27

where the trailing hexadecimal (everything after ``@``) indicates the
commit. You can find the latest upstream commit by visiting `the
executor
repository <https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__
and inspecting the commit history.

If the preceding steps did not update the installed version, you may
need to delete and rebuild your ``spras`` pixi environment.
