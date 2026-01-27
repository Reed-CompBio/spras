Running with HTCondor
=====================

The folder `htcondor/ <https://github.com/Reed-CompBio/spras/tree/main/htcondor>`_
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

Running all SPRAS steps on a single remote Execution Point (EP) is a good way
to get started with HTCondor, but it is significantly less efficient than using
HTCondor's distributed capabilities. This approach is best suited for
workflows that are not computationally intensive, or for testing and
debugging purposes.

Before submitting all SPRAS jobs to a single remote Execution Point (EP),
you'll need to set up three things:
1. You'll need to modify ``htcondor/spras.sub`` to point at your container
   image, along with any other configuration changes you want to make like
   choosing a logging directory or toggling OSPool submission. Note that all
   paths in the submit file are relative to the directory from which you run
   ``condor_submit``, which will typically be the root of the SPRAS repository.
2. You'll need to ensure your SPRAS configuration file has a few key values
   set, including ``unpack_singularity: true`` and
   ``containers.framework: singularity``.
3. Finally, it's best practice to create the logging directory configured in
   the submit file before submitting the job, e.g. to create the default log
   directory, run ``mkdir htcondor/logs`` from the root of the repository.

Once these steps are complete, you can submit the job from the root of the
the SPRAS repository by running ``condor_submit htcondor/spras.sub``.

When the job completes, the ``output`` directory from the workflow should be
returned as ``output``.

Submitting Parallel Jobs
------------------------

Parallelizing SPRAS workflows with HTCondor requires much of the same setup
as the previous section, but with several additions. 
1. Build/activate the SPRAS conda/mamba environment and ``pip install`` the SPRAS module
   (via ``pip install .`` inside the SPRAS directory).
2. Install the `HTCondor Snakemake
executor <https://github.com/htcondor/snakemake-executor-plugin-htcondor>`__; once your
   SPRAS conda/mamba environment is activated and SPRAS is ``pip install``-ed,
   you can install the HTCondor Snakemake executor with the following:

.. code:: bash

   pip install git+https://github.com/htcondor/snakemake-executor-plugin-htcondor.git

3. Instead of editing ``spras.sub`` to define the workflow, this scenario
   requires editing the SPRAS profile in ``htcondor/spras_profile/config.yaml``.
   Make sure you specify the correct container, and change any other config
   values needed by your workflow (defaults are fine in most cases).
4. Modify your SPRAS configuration file to set ``unpack_singularity: true`` and
   ``containers.framework: singularity``.

Then, to start the workflow with HTCondor in the CHTC pool, there are
two options:

Snakemake From Your Own Terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first option is to run Snakemake in a way that ties its execution to
your terminal. This is good for testing short workflows and running
short jobs. The downside is that closing your terminal causes the
process to exit, removing any unfinished jobs. To use this option,
invoke Snakemake directly from the repository root by running:

.. code:: bash

   snakemake --profile htcondor/spras_profile/

**Note**: Running the workflow in this way requires that your terminal
session stays active. Closing the terminal will suspend ongoing jobs, but
Snakemake will handle picking up where any previously-completed jobs left off
when you restart the workflow.

Long Running Snakemake Jobs (Managed by HTCondor)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

When executed in this mode, all log files for the workflow will be placed
into the logging directory (``htcondor/logs`` by default). In particular,
Snakemake's stdout/stderr outputs containing your workflow's progress can
be found split between ``htcondor/logs/snakemake.err`` and ``htcondor/logs/snakemake.out``.
These will also log each rule and what HTCondor job ID was submitted for
that rule (see the `troubleshooting section <#troubleshooting>`__ for
information on how to use these extra log files).

**Note**: While you're in the initial stages of developing/debugging your
workflow, it's very useful to invoke Snakemake with the ``--verbose`` flag.
This can be passed to Snakemake via the ``snakemake_long.py`` script by
adding it to the script's argument list, e.g.:

.. code:: bash

   ./htcondor/snakemake_long.py --profile htcondor/spras_profile/ --verbose

If you use mamba instead of conda for environment management, you can specify
this with the ``--env-manager`` flag:

.. code:: bash

   ./htcondor/snakemake_long.py --profile htcondor/spras_profile/ --env-manager mamba

Adjusting Resources
-------------------

Resource requirements can be adjusted as needed in
``htcondor/spras_profile/config.yaml``, and HTCondor logs for this workflow
can be found in your log directory. You can set a different log
directory by changing the configured ``htcondor-jobdir`` in the profile's
configuration. Alternatively, you can pass a different log directory
when invoking Snakemake with the ``--htcondor-jobdir`` argument.

To run this same workflow in the OSPool, add the following to the
profile's default-resources block:

::

     classad_WantGlideIn: true
     requirements: |
       '(HAS_SINGULARITY == True) && (Poolname =!= "CHTC")'

**Note**: If you encounter an error that says
``No module named 'spras'``, make sure you've ``pip install``-ed the
SPRAS module into your conda environment.

Job Monitoring
--------------

To monitor the state of the job, you can use a second terminal to run
``condor_q`` for a snapshot of how the workflow is doing, or you can run
``condor_watch_q`` for realtime updates.

Upon completion, the ``output`` directory from the workflow should be
returned as ``output``, along with several files containing the workflow's
logging information (anything that matches ``htcondor/logs/spras_*`` and
ending in ``.out``, ``.err``, or ``.log``). If the job was unsuccessful,
these files should contain useful debugging clues about what may have gone wrong.

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
executor bundled with your conda environment.

To upgrade, from your activated ``spras`` conda environment run:

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
need to delete and rebuild your ``spras`` conda environment.
