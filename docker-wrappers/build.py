import argparse
import json
import os
import subprocess
from pathlib import Path

COMMAND_BUILDX = ["docker", "buildx"]

COMMAND_BUILDER_LS = COMMAND_BUILDX + ["ls"]
COMMAND_BUILDER_INSTANCE = COMMAND_BUILDX + ["create", "--name", "container", "--driver=docker-container"]

# https://stackoverflow.com/a/5137509/7589775
dir_path = os.path.dirname(os.path.realpath(__file__))

def construct_push_command(
    tags: list[str],
    dir: str,
    architectures: list[str],
    push: bool,
    load: bool
) -> list[str]:
    """
    Constructs the docker command to be run by this script
    """
    base_cmd = ["build"]
    for tag in tags:
        base_cmd.extend(["--tag", tag])

    if push and load:
        raise RuntimeError("You specified both container pushing and container loading. Did you mean to test the container first?")

    base_cmd = base_cmd + [
        "--file",
        str(Path(dir_path, dir, "Dockerfile"))]

    if not load:
        # Add the architectures if load is not specified.
        base_cmd = base_cmd + ["--platform", ",".join(architectures)]

    base_cmd = base_cmd + ["--builder", "container"]

    if push: base_cmd.append("--push")
    if load: base_cmd.append("--load")

    # The 'local' directory: the CWD is set by the python code
    # running this function's output command.
    base_cmd.append(".")

    return COMMAND_BUILDX + base_cmd

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Docker Wrapper builder python wrapper"
    )
    parser.add_argument("--dir", type=str, required=True, help="The directory of the docker wrapper to use")
    parser.add_argument("--version", type=str, required=True, help="The version (tag name) to use for the container")
    parser.add_argument("--org-name", type=str, help="The organization to push to", default="ghcr.io/reed-compbio/")
    parser.add_argument("--yes", type=bool, help="Whether to automatically agree to pushing a container", action=argparse.BooleanOptionalAction)
    parser.add_argument("--relax", type=bool, help="Whether to not be strict on tag naming (this requires all versions start with `v`.)", action=argparse.BooleanOptionalAction)
    parser.add_argument("--push", type=bool, help="Enabling push pushes the image. Usually, images are only built locally.", action=argparse.BooleanOptionalAction)
    # This is a (sensible) limitation of docker: https://github.com/docker/buildx/issues/59. We don't say what architecture we want
    # to default to the system architecture.
    parser.add_argument("--load", type=bool, help="Enabling load adds a docker image to your local machine. This uses your local architecture.", action=argparse.BooleanOptionalAction)

    return parser.parse_args()

def main():
    # We need a buildx environment
    # This is a terrible check. Yes, docker buildx has no API exposed on docker-py.
    if f"\ncontainer" not in subprocess.check_output(COMMAND_BUILDER_LS).decode("utf-8"):
        out = subprocess.run(COMMAND_BUILDER_INSTANCE)
        if out.returncode != 0:
            raise RuntimeError(f"Command {COMMAND_BUILDER_INSTANCE} exited with non-zero exit code.")

    args = parse_arguments()

    if not args.org_name.endswith("/"):
        args.org_name = f"{args.org_name}/"

    if not args.version.startswith("v"):
        if not args.relax:
            raise ValueError("All versions start with v (v1, v2, ...)")

    metadata_path = Path(dir_path, args.dir, "metadata.json")
    metadata = json.loads(metadata_path.read_text())
    name = metadata['imageName']
    architectures = metadata['architectures']

    assert len(architectures) > 0, "you must specify at least one container architecture!"

    cwd = str(Path(dir_path, args.dir, metadata['cwd']) if 'cwd' in metadata else Path(dir_path, args.dir))
    tag = args.org_name + name + ":" + args.version
    tag_latest = args.org_name + name + ":latest"

    if args.load:
        print(f"Building {name} only on the system architecture with:")
    else:
        print(f"Building {name} over {architectures} with:")
    print(f"- CWD: {cwd}")
    print(f"- Specified tag: {tag}")
    print(f"-    Latest tag: {tag_latest}\n")
    if args.push:
        print("The docker images with the above tags will be _pushed_. (This command will also test all provided architectures beforehand.)")
    elif args.load:
        print("The docker images with the above tags will be _loaded_. This command will not test all provided architectures. To test, omit --load.")
    else:
        print("The docker images with the above tags will be _tested_. This command will not push (use --push) or allow this image to be used locally (use --load)")
    if not args.yes:
        confirm_string = "[y/n] Are you sure you want to do this? "
        confirm = input(confirm_string)
        if confirm.strip().lower() not in ('y', 'yes'):
            raise RuntimeError("Did not confirm dialog.")

    push_command = construct_push_command([tag, tag_latest], args.dir, architectures, push=args.push, load=args.load)
    result = subprocess.run(push_command, capture_output=False, cwd=cwd)

    exit(result.returncode)

if __name__ == '__main__':
    main()
