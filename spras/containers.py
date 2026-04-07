import os
import platform
import re
import subprocess
import textwrap
import warnings
from dataclasses import dataclass
from pathlib import Path, PurePath, PurePosixPath
from typing import Iterator, List, Optional, Tuple, Union

import docker
import docker.errors

from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings
from spras.logging import indent
from spras.profiling import create_apptainer_container_stats, create_peer_cgroup
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

class ContainerError(RuntimeError):
    """Raises when anything goes wrong inside a container"""

    error_code: int
    stdout: Optional[str]
    stderr: Optional[str]

    def __init__(self, message: str, error_code: int, stdout: Optional[str], stderr: Optional[str], *args):
        """
        Constructs a new ContainerError.

        @param message: The message to display to the user. This should usually refer to the indent call to differentiate between
        general logging done by Snakemake/logging calls.
        @param error_code: Also known as exit status; this should generally be non-zero for ContainerErrors.
        @param stdout: The standard output stream. If the origin of the stream is unknown, leave it in stdout.
        @param stderr: The standard error stream.
        """

        # https://stackoverflow.com/a/26938914/7589775
        self.message = message

        self.error_code = error_code
        self.stdout = stdout
        self.stderr = stderr

        super(ContainerError, self).__init__(message, error_code, stdout, stderr, *args)

    def streams_contain(self, needle: str):
        """
        Checks (with case sensitivity)
        if any of the stdout/err streams have the provided needle.
        """
        stdout = self.stdout if self.stdout else ''
        stderr = self.stderr if self.stderr else ''

        return (needle in stdout) or (needle in stderr)

    # Due to
    # https://github.com/snakemake/snakemake/blob/d4890b4da691506b6a258f7534ac41fdb7ef5ab4/src/snakemake/exceptions.py#L18
    # this overrides the tostr implementation to have nicer container errors
    def __str__(self):
        return self.message

def env_to_items(environment: dict[str, str]) -> Iterator[str]:
    """
    Turns an environment variable dictionary to KEY=VALUE pairs.
    """
    # TODO: we should also handle special escaping here.
    return (f"{key}={value}" for key, value in environment.items())


@dataclass(frozen=True)
class ResolvedImage:
    """Result of resolve_container_image().

    Carries the resolved image reference and whether it points to a local .sif file,
    so downstream code never needs to re-inspect image_override.
    """
    image: str          # registry URI (e.g. 'docker.io/reedcompbio/pathlinker:v2') or local .sif path
    is_local_sif: bool  # True when image is a local .sif file


def resolve_container_image(container_suffix: str, container_settings: ProcessedContainerSettings) -> ResolvedImage:
    """
    Resolve the container image from the algorithm's default suffix and any
    per-algorithm image override in container_settings.

    This is the single place where ``container_settings.image_override`` is
    inspected.  All downstream code (docker runner, singularity runner, dsub
    runner) receives the ``ResolvedImage`` or its ``.image`` string and never
    re-reads the override.

    Warnings are emitted for suspicious override patterns (excessive path depth,
    bare hostnames) and for .sif overrides on non-singularity frameworks.

    @param container_suffix: algorithm's default container name (e.g. 'pathlinker:v2')
    @param container_settings: the processed container settings (may include image_override)
    @return: a ResolvedImage with the image string and whether it's a local .sif
    """
    image_override = container_settings.image_override

    # Default: combine registry prefix with the algorithm's container suffix
    container = container_settings.prefix + "/" + container_suffix

    if image_override and image_override.endswith('.sif'):
        # .sif overrides are only meaningful for apptainer/singularity.
        if not container_settings.framework.is_singularity_family:
            warnings.warn(
                f"Image override '{image_override}' is a .sif file, but the container framework is "
                f"'{container_settings.framework}'. .sif overrides are only supported with "
                f"apptainer/singularity. Falling back to default image.",
                stacklevel=2
            )
            return ResolvedImage(image=container, is_local_sif=False)
        print(f'Container image override (local .sif): {image_override}', flush=True)
        return ResolvedImage(image=image_override, is_local_sif=True)
    elif image_override:
        # Image reference override — determine how much of the URI is specified.
        # Uses Docker's convention: if the first path component contains '.' or ':',
        # it's a registry hostname and the reference is fully qualified.
        if '/' in image_override:
            first_component = image_override.split('/')[0]
            if '.' in first_component or ':' in first_component:
                # Full registry reference like "ghcr.io/myorg/image:tag" — use as-is
                container = image_override
            else:
                # Owner/image like "some-other-owner/oi2:latest" — prepend base_url only
                container = container_settings.base_url + "/" + image_override
        else:
            # Image name only like "pathlinker:v1234" — prepend full prefix (base_url/owner)
            container = container_settings.prefix + "/" + image_override

        # Warn about suspicious override patterns that may indicate a typo or misconfiguration.
        # We still pass them through since they may be valid in unusual registries.
        parts = container.split('/')
        if len(parts) > 3:
            warnings.warn(
                f"Container image override '{image_override}' resolves to '{container}' "
                f"which has {len(parts)} path components. Standard container references "
                f"have at most 3 (registry/owner/image). This may be a misconfiguration. "
                f"Attempting to use '{container}' as-is.",
                stacklevel=2
            )
        elif '/' not in image_override and ':' not in image_override and '.' in image_override:
            warnings.warn(
                f"Container image override '{image_override}' looks like a hostname "
                f"without an image name or tag. Did you mean to include an image name "
                f"(e.g., '{image_override}/image:tag')? "
                f"Attempting to use '{container}' as-is.",
                stacklevel=2
            )

        print(f'Container image override: {container}', flush=True)
    else:
        print(f'Container image: {container}', flush=True)

    return ResolvedImage(image=container, is_local_sif=False)


# TODO consider a better default environment variable
# Follow docker-py's naming conventions (https://docker-py.readthedocs.io/en/stable/containers.html)
# Technically the argument is an image, not a container, but we use container here.
def run_container(container_suffix: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str | os.PathLike, container_settings: ProcessedContainerSettings, environment: Optional[dict[str, str]] = None, network_disabled = False):
    """
    Runs a command in the container using Singularity or Docker
    @param container_suffix: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param container_settings: the settings to use to run the container
    @param out_dir: output directory for the rule's artifacts. Only passed into run_container_singularity for the purpose of profiling.
    @param environment: environment variables to set in the container
    @param network_disabled: Disables the network on the container. Only works for docker for now. This acts as a 'runtime assertion' that a container works w/o networking.
    @return: output from Singularity execute or Docker run
    """
    resolved = resolve_container_image(container_suffix, container_settings)

    if container_settings.framework == ContainerFramework.docker:
        return run_container_docker(resolved.image, command, volumes, working_dir, environment, network_disabled)
    elif container_settings.framework.is_singularity_family:
        return run_container_singularity(resolved, command, volumes, working_dir, out_dir, container_settings, environment)
    elif container_settings.framework == ContainerFramework.dsub:
        return run_container_dsub(resolved.image, command, volumes, working_dir, environment)
    else:
        raise ValueError(f'{container_settings.framework} is not a recognized container framework. Choose "docker", "dsub", "apptainer", or "singularity".')

def run_container_and_log(name: str, container_suffix: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str | os.PathLike, container_settings: ProcessedContainerSettings, environment: Optional[dict[str, str]] = None, network_disabled=False):
    """
    Runs a command in the container using Singularity or Docker with associated pretty printed messages.
    @param name: the display name of the running container for logging purposes
    @param container_suffix: name of the DockerHub container without the 'docker://' prefix
    @param command: command to run in the container
    @param volumes: a list of volumes to mount where each item is a (source, destination) tuple
    @param working_dir: the working directory in the container
    @param container_settings: the container settings to use
    @param environment: environment variables to set in the container
    @param network_disabled: Disables the network on the container. Only works for docker for now. This acts as a 'runtime assertion' that a container works w/o networking.
    @return: output from Singularity execute or Docker run
    """
    if not environment:
        environment = {'SPRAS': 'True'}

    print('Running {} on container framework "{}" on env {} with command: {}'.format(name, container_settings.framework, list(env_to_items(environment)), ' '.join(command)), flush=True)
    try:
        out = run_container(container_suffix=container_suffix, command=command, volumes=volumes, working_dir=working_dir, out_dir=out_dir, container_settings=container_settings, environment=environment, network_disabled=network_disabled)
        if out is not None:
            if isinstance(out, list):
                out = ''.join(out)
            elif isinstance(out, dict):
                if 'message' in out:
                    # This is the format of a singularity message.
                    # See https://singularityhub.github.io/singularity-cli/api/source/spython.main.html?highlight=execute#spython.main.execute.execute.
                    exit_status = int(out['return_code']) if 'return_code' in out else 0
                    out = ''.join(out['message'])
                    if exit_status != 0:
                        message = f'An unexpected non-zero exit status ({exit_status}) occurred while running this singularity container:\n' + indent(out)
                        raise ContainerError(message, exit_status, out, None)
                else:
                    print("Note: The following output is an unknown message format which should be properly handled.")
                    print("Please file an issue at https://github.com/Reed-CompBio/spras/issues/new with this output.")
                    out = str(out)
            elif not isinstance(out, str):
                out = str(out, "utf-8")
            print(indent(out))
    except docker.errors.ContainerError as err:
        stdout = str(err.container.logs(stdout=True, stderr=False), 'utf-8')
        stderr = str(err.container.logs(stdout=False, stderr=True), 'utf-8')

        message = textwrap.dedent(f'''\
                                  (Command formatted as list: `{err.command}`)
                                  An unexpected non-zero exit status ({err.exit_status}) inside the docker image {err.image} occurred:\n''') + indent(stderr)
        # We retrieved all of the information from docker.errors.ContainerError, so here, we ignore the original error.
        raise ContainerError(message, err.exit_status, stdout, stderr) from None

# TODO any issue with creating a new client each time inside this function?
def run_container_docker(container: str, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, environment: Optional[dict[str, str]] = None, network_disabled=False):
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
                                network_disabled=network_disabled,
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
                                network_disabled=network_disabled,
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


def _prepare_singularity_image(resolved: ResolvedImage, config: ProcessedContainerSettings):
    """
    Prepare the image that apptainer/singularity should run.

    Handles sandbox unpacking and Docker URI prefixing.  Does **not** inspect
    ``config.image_override`` — all override logic is in ``resolve_container_image()``.

    Returns a path or URI suitable for Client.execute() or the profiling command.
    The four cases are:
      1. unpack + local .sif   --> unpack the .sif into a sandbox, return sandbox path
      2. unpack + registry     --> pull .sif from registry, unpack into sandbox, return sandbox path
      3. local .sif, no unpack --> return the .sif path directly
      4. registry, no unpack   --> return "docker://<image>" so apptainer pulls at runtime
    """
    from spython.main import Client

    if config.unpack_singularity:
        unpacked_dir = Path("unpacked")
        unpacked_dir.mkdir(exist_ok=True)

        if resolved.is_local_sif:
            # Use pre-built .sif directly, skip pulling from registry
            image_path = resolved.image
            base_cont = Path(resolved.image).stem
        else:
            # The incoming image string is of the format <repository>/<owner>/<image name>:<tag> e.g.
            # hub.docker.com/reedcompbio/spras:latest
            # Here we first produce a .sif image using the image name and tag (base_cont)
            # and then expand that image into a sandbox directory. For example,
            # hub.docker.com/reedcompbio/spras:latest --> spras_latest.sif --> ./spras_latest/
            path_elements = resolved.image.split("/")
            base_cont = path_elements[-1]
            base_cont = base_cont.replace(":", "_")
            sif_file = base_cont + ".sif"

            # Adding 'docker://' to the container indicates this is a Docker image Singularity must convert
            image_path = Client.pull('docker://' + resolved.image, name=str(unpacked_dir / sif_file))

        base_cont_path = unpacked_dir / Path(base_cont)

        # Check whether the directory for base_cont_path already exists. When running concurrent jobs, it's possible
        # something else has already pulled/unpacked the container.
        # Here, we expand the sif image from `image_path` to a directory indicated by `base_cont_path`
        if not base_cont_path.exists():
            Client.build(recipe=image_path, image=str(base_cont_path), sandbox=True, sudo=False)
        print(f'Resolved singularity image to sandbox: {base_cont_path}', flush=True)
        return base_cont_path  # sandbox directory

    if resolved.is_local_sif:
        # Local .sif without unpacking — use directly
        print(f'Resolved singularity image to local .sif: {resolved.image}', flush=True)
        return resolved.image

    # No override, no unpacking — apptainer pulls and converts the Docker image at runtime
    docker_uri = "docker://" + resolved.image
    print(f'Resolved singularity image: {docker_uri}', flush=True)
    return docker_uri


def run_container_singularity(resolved: ResolvedImage, command: List[str], volumes: List[Tuple[PurePath, PurePath]], working_dir: str, out_dir: str, config: ProcessedContainerSettings, environment: Optional[dict[str, str]] = None):
    """
    Runs a command in the container using Singularity.
    Only available on Linux.
    @param resolved: the resolved container image (registry URI or local .sif path)
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

    image_to_run = _prepare_singularity_image(resolved, config)

    if config.enable_profiling:
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

        my_cgroup = create_peer_cgroup()
        # The wrapper script is packaged with spras, and should be located in the same directory
        # as `containers.py`.
        wrapper = os.path.join(os.path.dirname(__file__), "cgroup_wrapper.sh")
        cmd = [wrapper, my_cgroup] + singularity_cmd
        proc = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)

        print("Reading memory and CPU stats from cgroup")
        create_apptainer_container_stats(my_cgroup, out_dir)

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
def prepare_volume(filename: Union[str, os.PathLike], volume_base: Union[str, PurePath], config: ProcessedContainerSettings) -> Tuple[Tuple[PurePath, PurePath], str]:
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

    if isinstance(filename, os.PathLike):
        filename = str(filename)

    filename_hash = hash_filename(filename, config.hash_length)
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
