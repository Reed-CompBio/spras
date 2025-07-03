import argparse
import subprocess
import os
import json
from pathlib import Path

COMMAND_BUILDX = ["docker", "buildx"]

COMMAND_BUILDER_LS = COMMAND_BUILDX + ["ls"]
COMMAND_BUILDER_INSTANCE = COMMAND_BUILDX + ["create", "--name", "container", "--driver=docker-container"]

# https://stackoverflow.com/a/5137509/7589775
dir_path = os.path.dirname(os.path.realpath(__file__))

def construct_push_command(tag: str, dir: str):
    base_cmd = ["build", "--tag", tag, "--file", Path(dir_path, dir, "Dockerfile"), "--platform",
                "linux/arm64,linux/amd64", "--builder", "container", "--push", "."]
    return COMMAND_BUILDX + base_cmd

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Docker Wrapper builder python wrapper"
    )
    parser.add_argument("--dir", type=str, required=True, help="The directory of the docker wrapper to use")
    parser.add_argument("--version", type=str, required=True, help="The version (tag name) to use for the container")
    parser.add_argument("--org-name", type=str, help="The organization to push to", default="ghcr.io/reed-compbio/")
    parser.add_argument("--yes", type=bool, help="Whether to automatically agree to pushing a container")
    parser.add_argument("--relax", type=bool, help="Whether to not be strict on tag naming")

    return parser.parse_args()

def main():
    # We need a buildx environment
    # This is a terrible check. Yes, docker buildx has no API exposed on docker-py.
    if not f"\ncontainer" in subprocess.check_output(COMMAND_BUILDER_LS).decode("utf-8"):
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
    name = json.loads(metadata_path.read_text())['dockerName']
    tag = args.org_name + name + ":" + args.version

    push_command = construct_push_command(tag, args.dir)

    if not args.yes:
        confirm = input(f"[y/n] Are you sure you want to push to {tag}? ")
        if confirm.strip().lower() not in ('y', 'yes'):
            raise RuntimeError("Did not confirm dialog.")
    subprocess.run(push_command, capture_output=False)

if __name__ == '__main__':
    main()
