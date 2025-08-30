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
    push: bool
):
    base_cmd = ["build"]
    for tag in tags:
        base_cmd.extend(["--tag", tag])
    base_cmd = base_cmd + ["--file", Path(dir_path, dir, "Dockerfile"), "--platform",
                ",".join(architectures), "--builder", "container"]
    if push:
        base_cmd.append("--push")
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
    parser.add_argument("--nopush", type=bool, help="Enabling nopush only builds the image. This is useful for testing architecture support", action=argparse.BooleanOptionalAction)

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
    cwd = str(Path(dir_path, args.dir, metadata['cwd']) if 'cwd' in metadata else Path(dir_path, args.dir))
    tag = args.org_name + name + ":" + args.version
    tag_latest = args.org_name + name + ":latest"

    print(f"Building {name} over {architectures} with:")
    print(f"- CWD: {cwd}")
    print(f"- Specified tag: {tag}")
    print(f"-    Latest tag: {tag_latest}")
    if not args.yes:
        confirm = input("[y/n] Are you sure you want to {} these tags over these architectures? ".format("build (because of --nopush)" if args.nopush else "push to"))
        if confirm.strip().lower() not in ('y', 'yes'):
            raise RuntimeError("Did not confirm dialog.")

    push_command = construct_push_command([tag, tag_latest], args.dir, architectures, not args.nopush)
    result = subprocess.run(push_command, capture_output=False, cwd=cwd)

    exit(result.returncode)

if __name__ == '__main__':
    main()
