import csv
import os


def create_peer_cgroup() -> str:
    """
    A helper function that creates a new peer cgroup for the current process.
    Apptainer/singularity containers are placed in this cgroup so that they
    can be tracked for memory and CPU usage.
    This currently assumes HTCondor runs where the current process is already
    in a two-level nested cgroup (introduced in HTCondor 24.8.0).

    Returns the path to the peer cgroup, which is needed by the cgroup_wrapper.sh script
    to set up the cgroup for the container.
    """

    # Get the current process's cgroup path
    # This assumes the cgroup is in the unified hierarchy
    with open("/proc/self/cgroup") as f:
        first_line = next(f).strip()
        cgroup_rel = first_line.split(":")[-1].strip()

    mycgroup = os.path.join("/sys/fs/cgroup", cgroup_rel.lstrip("/"))
    peer_cgroup = os.path.join(os.path.dirname(mycgroup), f"spras-peer-{os.getpid()}")

    # Create the peer cgroup directory
    try:
        os.makedirs(peer_cgroup, exist_ok=True)
    except Exception as e:
        print(f"Failed to create cgroup: {e}")

    return peer_cgroup


def create_apptainer_container_stats(cgroup_path: str, out_dir: str):
    """
    Reads the contents of the provided cgroup's memory.peak and cpu.stat files.
    This information is parsed and placed in the calling rule's output directory
    as 'usage-profile.tsv'.
    @param cgroup_path: path to the cgroup directory for the container
    @param out_dir: output directory for the rule's artifacts -- used here to store profiling data
    """

    profile_path = os.path.join(out_dir, "usage-profile.tsv")

    peak_mem = "N/A"
    try:
        with open(os.path.join(cgroup_path, "memory.peak")) as f:
            peak_mem = f.read().strip()
    except Exception as e:
        print(f"Failed to read memory usage from cgroup: {e}")

    cpu_usage = cpu_user = cpu_system = "N/A"
    try:
        with open(os.path.join(cgroup_path, "cpu.stat")) as f:
            # Parse out the contents of the cpu.stat file
            # You can find these fields by searching "cpu.stat" in the cgroup documentation:
            # https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
            for line in f:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                key, value = parts
                if key == "usage_usec":
                    cpu_usage = value
                elif key == "user_usec":
                    cpu_user = value
                elif key == "system_usec":
                    cpu_system = value
    except Exception as e:
        print(f"Failed to read cpu.stat from cgroup: {e}")

    # Set up the header for the TSV file
    header = ["peak_memory_bytes", "cpu_usage_usec", "cpu_user_usec", "cpu_system_usec"]
    row = [peak_mem, cpu_usage, cpu_user, cpu_system]

    # Write the contents of the file
    write_header = not os.path.exists(profile_path) or os.path.getsize(profile_path) == 0
    with open(profile_path, "a", newline="") as out_f:
        writer = csv.writer(out_f, delimiter="\t")

        # Only write the header if the file was previously empty or did not exist
        if write_header:
            writer.writerow(header)
        writer.writerow(row)

