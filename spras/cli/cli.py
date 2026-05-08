import argparse
import itertools
import os
import subprocess
from pathlib import Path

# https://stackoverflow.com/a/5137509/7589775
# The file we want, Snakefile, is also included in MANIFEST.in
dir_path = os.path.dirname(os.path.realpath(__file__))
# we resolve to simplify the path name in errors
snakefile_path = Path(dir_path, "..", "Snakefile").resolve()

# Removes the very awkwardly phrased "{subcommand1, subcommand2}" from the subcommand help
# from https://stackoverflow.com/a/13429281/7589775
class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        parts = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts

def get_parser():
    parser = argparse.ArgumentParser(
                    prog='SPRAS',
                    description='The wrapping tool for SPRAS (signaling pathway reconstruction analysis streamliner)',
                    epilog='SPRAS is in alpha. Report issues or suggest features on GitHub: https://github.com/Reed-CompBio/spras',
                    formatter_class=SubcommandHelpFormatter)

    subparsers = parser.add_subparsers(title='subcommands',
                                       help='subcommand help',
                                       dest='subcommand')
    subparsers = subparsers.add_parser('run',
                                       help='Run the SPRAS Snakemake workflow',
                                       # We let snakemake handle help
                                       add_help=False)

    return parser

def run():
    parser = get_parser()
    (args, unknown_args) = parser.parse_known_args()

    if args.subcommand == "run":
        subprocess.run(list(itertools.chain(
            ["snakemake", "-s", snakefile_path],
            unknown_args
        )))
        return

    parser.print_help()

if __name__ == '__main__':
    run()
