from setuptools import setup
import subprocess
from pathlib import Path

spras_version = '0.6.0'

# All of this was modified from https://stackoverflow.com/a/77001804/7589775.
current_directory = Path(__file__).parent.resolve()

try:
    commit_version = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        encoding='utf-8',
        # In case the CWD is not inside the actual SPRAS directory
        cwd=Path(__file__).parent.resolve()
    ).strip()
except FileNotFoundError:
    # git wasn't found. As to be expected!
    commit_version = None
except subprocess.CalledProcessError:
    # no git repository was found. This is also fine!
    commit_version = None

setup(
    # Versions must be in semantic commit format: we dynamically change the version to be
    # a faux dev version (which triggers during git-based pip installs, submodule clones, and SPRAS development.)
    # (Note that git commit hashes are in hex, so this cast is safe)
    version=f"0.0.{int(commit_version, 16)}" if commit_version else f"{spras_version}"
)
