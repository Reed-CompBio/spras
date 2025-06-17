import csv
import os
import platform
import re
import subprocess
from pathlib import Path, PurePath, PurePosixPath
from typing import Iterator, List, Optional, Tuple, Union

import docker
import docker.errors

import spras.config.config as config
from spras.logging import indent
from spras.util import hash_filename


def prepare_path_docker(orig_path: PurePath) -> str:
    """
    Prepare an absolute path for mounting as a Docker volume.
    Converts Windows file separators to posix separators.
    Converts Windows drive letters in absolute paths.
    """
    # TODO consider testing PurePath.is_absolute()
    prepared_path = orig_path.as_posix()
    # Check whether the path matches an absolute Windows path with a drive letter
    match = re.match(r'^([A-Z]:)(.*)', prepared_path)
    if match:
        # The first group is the drive such as C:
        drive = match.group(1).lower()[0]
        # The second group is the rest of the path such as /Users/me
        prepared_path = match.group(2)
        prepared_path = '//' + drive + prepared_path
    return prepared_path


def convert_docker_path(src_path: PurePath, dest_path: PurePath, file_path: Union[str, PurePath]) -> PurePosixPath:
    """
    Convert a file_path that is in src_path to be in dest_path instead.
    For example, convert /usr/mydir and /usr/mydir/myfile and /tmp to /tmp/myfile
    @param src_path: source path that is a parent of file_path
    @param dest_path: destination path
    @param file_path: filename that is under the source path
    @return: a new path with the filename relative to the destination path
    """
    rel_path = file_path.relative_to(src_path)
    return PurePosixPath(dest_path, rel_path)


def download_gcs(gcs_path: str, local_path: str, is_dir: bool):
    # check that output path exists
    if not os.path.exists(Path(local_path).parent):
        os.makedirs(Path(local_path).parent)

    # build command
    cmd = 'gcloud storage'
    # rsync with checksums to make file transfer faster for larger files
    cmd = cmd + ' rsync --checksums-only'
    # check if directory
    if is_dir:
        cmd = cmd + ' -r'
    cmd = cmd + ' ' + gcs_path + ' ' + local_path

    print(cmd)
    # run command
    subprocess.run(cmd, shell=True)

    if Path(Path(local_path)/'gcs_temp.txt').exists():
        Path(Path(local_path)/'gcs_temp.txt').unlink()


def upload_gcs(local_path: str, gcs_path: str, is_dir: bool):
    # check if path exists in cloud storage
    exists = len(subprocess.run(f'gcloud storage ls {gcs_path}', shell=True, capture_output=True, text=True).stdout)
    # if path exists rsync
    if exists > 0:
        cmd = 'gcloud storage rsync --checksums-only'
    # if directory is empty
    elif exists == 0 and len(os.listdir(local_path)) == 0:
        # create a temporary file because GCS will not recognize empty directories
        Path(Path(local_path)/'gcs_temp.txt').touch()
        # copy path to cloud storage
        cmd = 'gcloud storage cp -c'
    # else copy path to cloud storage
    else:
        cmd = 'gcloud storage cp -c'
    # check if directory
    if is_dir:
        cmd = cmd + ' -r'
    cmd = cmd + ' ' + str(Path(local_path).resolve()) + ' ' + gcs_path

    print(cmd)
    # run command
    subprocess.run(cmd, shell=True)


def prepare_dsub_cmd(flags: dict[str, str | list[str]]):
    # set constant flags
    dsub_command = 'dsub'
    flags['provider'] = 'google-cls-v2'
    flags['regions'] = 'us-central1'
    flags['user-project'] = os.getenv('GOOGLE_PROJECT')
    flags['project'] = os.getenv('GOOGLE_PROJECT')
    flags['network'] = 'network'
    flags['subnetwork'] = 'subnetwork'
    flags['service-account'] = subprocess.run(['gcloud', 'config', 'get-value', 'account'], capture_output=True, text=True).stdout.replace('\n', '')

    # order flags according to flag_list
    flag_list = ["provider", "regions", "zones", "location", "user-project", "project", "network", "subnetwork", "service-account", "image", "env",
                 "logging", "input", "input-recursive", "mount", "output", "output-recursive", "command", "script"]
    ordered_flags = {f:flags[f] for f in flag_list if f in flags.keys()}

    # iteratively add flags to the command
    for flag, value in ordered_flags.items():
        if isinstance(value, list):
            for f in value:
                dsub_command = dsub_command + " --" + flag + " " + f
        else:
            dsub_command = dsub_command + " --" + flag + " " + value

    # Wait for dsub job to complete
    dsub_command = dsub_command + " --wait"
    print(f"dsub command: {dsub_command}")
    return dsub_command

def env_to_items(environment: dict[str, str]) -> Iterator[str]:
    """
    Turns an environment variable dictionary to KEY=VALUE pairs.
    """
    # TODO: we should also handle special escaping here.
    return (f"{key}={value}" for key, value in environment.items())

# TODO consider a better default environment variable
# Follow docker-py's naming conventions (https://docker-py.readthedocs.io/en/stable/containers.html)
# Technically the argument is an image, not a container, but we use container here.
def run_container(framework: str, container_suffix: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str | os.PathLike, environment: Optional[dict[str, str]] = None):
    """
    Runs a command in the container using Singularity or Docker
    @param framework: singularity or docker
    @param container_suffix: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param environment: environment variables to set in the container
    @param out_dir: output directory for the rule's artifacts. Only passed onto run_container_singularity for the purpose of profiling.
    @return: output from Singularity execute or Docker run
    """
    normalized_framework = framework.casefold()

    container = config.config.container_prefix + "/" + container_suffix
    if normalized_framework == 'docker':
        return run_container_docker(container, command, volumes, working_dir, environment)
    elif normalized_framework == 'singularity' or normalized_framework == "apptainer":
        return run_container_singularity(container, command, volumes, working_dir, out_dir, environment)
    elif normalized_framework == 'dsub':
        return run_container_dsub(container, command, volumes, working_dir, environment)
    else:
        raise ValueError(f'{framework} is not a recognized container framework. Choose "docker", "dsub", or "singularity".')

def run_container_and_log(name: str, framework: str, container_suffix: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str | os.PathLike, environment: Optional[dict[str, str]] = None):
    """
    Runs a command in the container using Singularity or Docker with associated pretty printed messages.
    @param name: the display name of the running container for logging purposes
    @param framework: singularity or docker
    @param container_suffix: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param environment: environment variables to set in the container
    @return: output from Singularity execute or Docker run
    """
    if not environment:
        environment = {'SPRAS': 'True'}

    print('Running {} on container framework "{}" on env {} with command: {}'.format(name, framework, list(env_to_items(environment)), ' '.join(command)), flush=True)
    try:
        out = run_container(framework=framework, container_suffix=container_suffix, command=command, volumes=volumes, working_dir=working_dir, out_dir=out_dir, environment=environment)
        if out is not None:
            if isinstance(out, list):
                out = ''.join(out)
            elif isinstance(out, dict):
                if 'message' in out:
                    # This is the format of a singularity message.
                    # See https://singularityhub.github.io/singularity-cli/api/source/spython.main.html?highlight=execute#spython.main.execute.execute.
                    if 'return_code' in out and not out['return_code'] == 0:
                        print(f"(Program exited with non-zero exit code '{out['return_code']}')")
                    out = ''.join(out['message'])
                else:
                    print("Note: This is an unknown message format - if you want this pretty printed, please file an issue at https://github.com/Reed-CompBio/spras/issues/new.")
                    out = str(out)
            elif not isinstance(out, str):
                out = str(out, "utf-8")
            print(indent(out))
    except docker.errors.ContainerError as err:
        print(f"(Command formatted as list: `{err.command}`)")
        print(f"An unexpected non-zero exit status ({err.exit_status}) inside the docker image {err.image} occurred:")
        err = str(err.stderr if err.stderr is not None else "", "utf-8")
        print(indent(err))
    except Exception as err:
        raise err

# TODO any issue with creating a new client each time inside this function?
def run_container_docker(container: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, environment: Optional[dict[str, str]] = None):
    """
    Runs a command in the container using Docker.
    Attempts to automatically correct file owner and group for new files created by the container, setting them to the
    current owner and group IDs.
    Does not modify the owner or group for existing files modified by the container.
    @param container: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param environment: environment variables to set in the container
    @return: output from Docker run, or will error if the container errored.
    """

    if not environment:
        environment = {'SPRAS': 'True'}

    # Initialize a Docker client using environment variables
    try:
        client = docker.from_env()
    except Exception as err:
        err.add_note("An error occurred when fetching the docker daemon: is docker installed and is dockerd running?")
        raise err
    # Track the contents of the local directories that will be bound so that new files added can have their owner
    # changed
    pre_volume_contents = {}
    src_dest_map = {}
    for src, dest in volumes:
        src_path = Path(src)
        # The same source path can be in volumes more than once if there were multiple input or output files
        # in the same directory
        # Only check each unique source path once and track which of the possible destination paths was used
        if src_path not in pre_volume_contents:
            # Only list files in the directory, do not walk recursively because it could include
            # a massive number of files
            pre_volume_contents[src_path] = set(src_path.iterdir())
            src_dest_map[src_path] = dest

    bind_paths = [f'{prepare_path_docker(src)}:{dest}' for src, dest in volumes]

    out = client.containers.run(container,
                                command,
                                stderr=True,
                                volumes=bind_paths,
                                working_dir=working_dir,
                                environment=environment).decode('utf-8')

    # TODO does this cleanup need to still run even if there was an error in the above run command?
    # On Unix, files written by the above Docker run command will be owned by root and cannot be modified
    # outside the container by a non-root user
    # Reset the file owner and the group inside the container
    try:
        # Only available on Unix
        uid = os.getuid()
        gid = os.getgid()

        all_modified_volume_contents = set()
        for src_path in pre_volume_contents.keys():
            # Assumes the Docker run call is the only process that modified the contents
            # Only considers files that were added, not files that were modified
            post_volume_contents = set(src_path.iterdir())
            modified_volume_contents = post_volume_contents - pre_volume_contents[src_path]
            modified_volume_contents = [str(convert_docker_path(src_path, src_dest_map[src_path], p)) for p in
                                        modified_volume_contents]
            all_modified_volume_contents.update(modified_volume_contents)

        # This command changes the ownership of output files so we don't
        # get a permissions error when snakemake or the user try to touch the files
        # Use --recursive because new directories could have been created inside the container
        # Do not run the command if no files were modified
        if len(all_modified_volume_contents) > 0:
            chown_command = ['chown', f'{uid}:{gid}', '--recursive']
            chown_command.extend(all_modified_volume_contents)
            chown_command = ' '.join(chown_command)
            client.containers.run(container,
                                chown_command,
                                stderr=True,
                                volumes=bind_paths,
                                working_dir=working_dir,
                                environment=environment).decode('utf-8')

    # Raised on non-Unix systems
    except AttributeError:
        pass

    # TODO: Not sure whether this is needed or where to close the client
    client.close()
    # Removed the finally block to address bugbear B012
    # "`return` inside `finally` blocks cause exceptions to be silenced"
    # finally:
    return out


def create_cgroup() -> str:
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


def create_container_stats(cgroup_path: str, out_dir: str):
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


def run_container_singularity(container: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str, environment: Optional[dict[str, str]] = None):
    """
    Runs a command in the container using Singularity.
    Only available on Linux.
    @param container: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param out_dir: output directory for the rule's artifacts -- used here to store profiling data
    @param environment: environment variable to set in the container
    @return: output from Singularity execute
    """

    if not environment:
        environment = {'SPRAS': 'True'}

    # spython is not compatible with Windows
    if platform.system() != 'Linux':
        raise NotImplementedError('Singularity support is only available on Linux')

    # See https://stackoverflow.com/questions/3095071/in-python-what-happens-when-you-import-inside-of-a-function
    from spython.main import Client

    bind_paths = [f'{prepare_path_docker(src)}:{dest}' for src, dest in volumes]

    # TODO is try/finally needed for Singularity?
    # To debug a container add the execute arguments: singularity_options=['--debug'], quiet=False
    singularity_options = ['--cleanenv', '--containall', '--pwd', working_dir]
    # Singularity does not allow $HOME to be set as a regular environment variable
    # Capture it and use the special argument instead
    if 'HOME' in environment:
        home_dir = environment['HOME']
        singularity_options.extend(['--home', home_dir])
        # We delete HOME to avoid adding it to `--env` right after.
        del environment['HOME']

    # https://docs.sylabs.io/guides/3.7/user-guide/environment_and_metadata.html#env-option
    singularity_options.extend(['--env', ",".join(env_to_items(environment))])

    expanded_image = None
    if config.config.unpack_singularity:
        path_elements = container.split("/")
        base_cont = path_elements[-1]
        base_cont = base_cont.replace(":", "_").split(":")[0]
        sif_file = base_cont + ".sif"

        # To allow caching unpacked singularity images without polluting git on local runs,
        # we move all of the unpacked image files into a `.gitignore`d folder.
        unpacked_dir = Path("unpacked")
        unpacked_dir.mkdir(exist_ok=True)

        # Adding 'docker://' to the container indicates this is a Docker image Singularity must convert
        image_path = Client.pull('docker://' + container, name=str(unpacked_dir / sif_file))

        base_cont_path = unpacked_dir / Path(base_cont)

        # Check whether the directory for base_cont_path already exists. When running concurrent jobs, it's possible
        # something else has already pulled/unpacked the container.
        # Here, we expand the sif image from `image_path` to a directory indicated by `base_cont_path`
        if not base_cont_path.exists():
            Client.build(recipe=image_path, image=str(base_cont_path), sandbox=True, sudo=False)
        expanded_image = base_cont_path  # This is the sandbox directory

    # If not using the expanded sandbox image, we still need to prepend the docker:// prefix
    # so apptainer knows to pull the image.
    image_to_run = expanded_image if expanded_image else "docker://" + container
    if config.config.enable_profiling:
        # We won't end up using the spython client if profiling is enabled because
        # we need to run everything manually to set up the cgroup
        # Build the apptainer run command, which gets passed to the cgroup wrapper script
        singularity_cmd = [
            "apptainer", "exec"
        ]
        for bind in bind_paths:
            singularity_cmd.extend(["--bind", bind])
        singularity_cmd.extend(singularity_options)
        singularity_cmd.append(image_to_run)
        singularity_cmd.extend(command)

        my_cgroup = create_cgroup()
        # The wrapper script is packaged with spras, and should be located in the same directory
        # as `containers.py`.
        wrapper = os.path.join(os.path.dirname(__file__), "cgroup_wrapper.sh")
        cmd = [wrapper, my_cgroup] + singularity_cmd
        proc = subprocess.run(cmd, capture_output=True, text=True)
        print("Stdout from container execution:", proc.stdout)

        print("Reading memory and CPU stats from cgroup")
        create_container_stats(my_cgroup, out_dir)

        result = proc.stdout
    else:
        result = Client.execute(
            image=image_to_run,
            command=command,
            options=singularity_options,
            bind=bind_paths
        )

    return result


# Because this is called independently for each file, the same local path can be mounted to multiple volumes
def prepare_volume(filename: Union[str, PurePath], volume_base: Union[str, PurePath]) -> Tuple[Tuple[PurePath, PurePath], str]:
    """
    Makes a file on the local file system accessible within a container by mapping the local (source) path to a new
    container (destination) path and renaming the file to be relative to the destination path.
    The destination path will be a new path relative to the volume_base that includes a hash identifier derived from the
    original filename.
    An example mapped filename looks like '/spras/MG4YPNK/oi1-edges.txt'.
    @param filename: The file on the local file system to map
    @param volume_base: The base directory in the container, which must be an absolute directory
    @return: first returned object is a tuple (source path, destination path) and the second returned object is the
    updated filename relative to the destination path
    """
    base_path = PurePosixPath(volume_base)
    if not base_path.is_absolute():
        raise ValueError(f'Volume base must be an absolute path: {volume_base}')

    if isinstance(filename, PurePath):
        filename = str(filename)

    filename_hash = hash_filename(filename, config.config.hash_length)
    dest = PurePosixPath(base_path, filename_hash)

    abs_filename = Path(filename).resolve()
    container_filename = str(PurePosixPath(dest, abs_filename.name))
    if abs_filename.is_dir():
        dest = PurePosixPath(dest, abs_filename.name)
        src = abs_filename
    else:
        parent = abs_filename.parent
        if parent.as_posix() == '.':
            parent = Path.cwd()
        src = parent

    return (src, dest), container_filename


def run_container_dsub(container: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, environment: Optional[dict[str, str]] = None) -> str:
    """
    Runs a command in the Google Cloud using dsub.
    @param container: name of the container in the Google Cloud Container Registry
    @param command: command to run
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param environment: environment variables to set in the container
    @return: path of output from dsub
    """
    if not environment:
        environment = {'SPRAS': 'True'}

    # Dictionary of flags for dsub command
    flags = dict()

    workspace_bucket = os.getenv('WORKSPACE_BUCKET')
    if not workspace_bucket:
        raise RuntimeError("The environment variable 'WORKSPACE_BUCKET' was not specified.")
    # Add path in the workspace bucket and label for dsub command for each volume
    dsub_volumes = [(src, dst, workspace_bucket + str(dst), "INPUT_" + str(i),) for i, (src, dst) in enumerate(volumes)]

    # Prepare command that will be run inside the container for dsub
    container_command = list()
    for item in command:
        # Find if item is volume
        to_replace = [(str(path[1]), "${"+path[3]+'}') for path in dsub_volumes if str(path[1]) in item]
        # Replace volume path with dsub volume path
        if len(to_replace) == 1:
            # Get path that will be replaced
            path = to_replace[0][0]
            # Get dsub input variable that will replace path
            env_variable = to_replace[0][1]
            # Replace path with env_variable
            container_path = item.replace(path, env_variable)
            # Add / if there is no suffix
            if container_path == env_variable:
                container_path = container_path + '/'
            container_command.append(container_path)
        else:
            container_command.append(item)

    # Add a command to copy the volumes to the workspace buckets
    container_command.append(('; cp -rf ' + f'/mnt/data/input/gs/{workspace_bucket}{working_dir}/*' + ' $OUTPUT').replace('gs://', ''))

    # Make the command into a string
    flags['command'] = ' '.join(container_command)
    flags['command'] = "'" + flags['command'] + "'"

    # Push volumes to WORKSPACE_BUCKET
    for src, _dst, gcs_path, _env in dsub_volumes:
        upload_gcs(local_path=str(src), gcs_path=gcs_path, is_dir=True)

    # Prepare flags for dsub command
    flags['image'] = container
    # https://github.com/DataBiosphere/dsub/tree/030589190ca9df85935cf68de556c2fbd4bad30d?tab=readme-ov-file#passing-parameters-to-your-script
    flags['env'] = list(env_to_items(environment))
    flags['input-recursive'] = [vol[3]+'='+vol[2] for vol in dsub_volumes]
    flags['output-recursive'] = "OUTPUT=" + workspace_bucket + working_dir
    flags['logging'] = workspace_bucket + '/dsub/'

    # Create dsub command
    dsub_command = prepare_dsub_cmd(flags)

    # Run dsub as subprocess
    subprocess.run(dsub_command, shell=True)

    # Pull output volumes from WORKSPACE_BUCKET
    for src, _dst, gcs_path, _env in dsub_volumes:
        download_gcs(local_path=str(src), gcs_path=gcs_path, is_dir=True)

    # return location of dsub logs in WORKSPACE_BUCKET
    return 'dsub logs: {logs}'.format(logs=flags['logging'])
