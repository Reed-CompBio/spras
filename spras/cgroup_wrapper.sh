#!/bin/bash

# This script gets invoked by run_singularity_container when enable_profiling is set to true.
# Its purpose is to move its own PID into the specified cgroup and then execute the container commands
# passed to it. This has the effect of sticking all processes started by the container into the specified
# cgroup, which lets us monitor them all in aggregate for resource usage.

CGROUP_PATH="$1"
echo "My cgroup path is: $CGROUP_PATH"
shift
echo $$ > "$CGROUP_PATH/cgroup.procs"

echo "Executing command: $@"
exec "$@"
