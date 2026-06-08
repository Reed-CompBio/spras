#!/bin/bash

# Fail early if there's an issue
set -e

# When .cache files are created, they need to know where HOME is to write there.
# In this case, that should be the HTCondor scratch dir the job is executing in.
export HOME=$(pwd)
# Various other apptainer-related environment variables that can causes problems
# if not explicitly set. These came from testing/debugging workflows on the
# OSPool.
export APPTAINER_CACHEDIR=$(pwd)
export APPTAINER_TMPDIR=$(pwd)
mkdir -p "$APPTAINER_TMPDIR"
unset SINGULARITY_BIND APPTAINER_BIND
unset SINGULARITY_TMPDIR

snakemake "$@"
