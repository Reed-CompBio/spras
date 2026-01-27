#!/usr/bin/env bash

# Example helper script to submit a SPRAS workflow to HTCondor with full parallelization
#
# Note that for full runs after any initial debugging, you may wish to remove the `--verbose`
# flag, as this significantly increases the size of log files

./htcondor/snakemake_long.py --profile htcondor/spras_profile/ --verbose
