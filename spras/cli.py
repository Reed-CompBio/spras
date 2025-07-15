import itertools
import os
import subprocess
import sys
from pathlib import Path

# https://stackoverflow.com/a/5137509/7589775
# The file we want, visjs.html, is also included in MANIFEST.in
dir_path = os.path.dirname(os.path.realpath(__file__))
snakefile_path = Path(dir_path, "..", "Snakefile")

def run():
    subprocess.run(list(itertools.chain(
        ["snakemake", "-s", snakefile_path],
        sys.argv[1:]
    )))

if __name__ == '__main__':
    run()
