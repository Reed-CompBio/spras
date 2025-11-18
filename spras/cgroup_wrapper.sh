#!/bin/bash

# This script gets invoked by run_singularity_container when enable_profiling is set to true.
# Its arguments are <cgroup_path> <apptainer exec command and args>
# If profiling is enabled, we've already created a new cgroup that has no running processes and
# we've started this script with its own PID. To isolate the inner container's resource usage stats,
# we add this script's PID to the new cgroup and then run the apptainer command. Since the generic
# snakemake/spras stuff is outside this cgroup, we can monitor the inner container's resource usage
# without conflating it with the overhead from spras itself.

CGROUP_PATH="$1"
echo "My cgroup path is: $CGROUP_PATH"
# Pop the first argument off the list so remaining args are just the apptainer command to exec
shift
echo $$ > "$CGROUP_PATH/cgroup.procs"

# Start apptainer
echo "Executing command: $@"
exec "$@"
