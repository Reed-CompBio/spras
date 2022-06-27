import argparse
# defined command line options
# this also generates --help and error handling
CLI=argparse.ArgumentParser()
CLI.add_argument(
  "--lista",  # name on the CLI - drop the `--` for positional/required parameters
  nargs="*",  # 0 or more values expected => creates a list
  type=int,
  default=[1, 2, 3],  # default if nothing is provided
)
CLI.add_argument(
  "--listb",
  nargs="*",
  type=float,  # any type/callable can be used here
  default=[],
)

# parse the command line
args = CLI.parse_args()
# access CLI options
print("lista: %r" % args.lista)
print("listb: %r" % args.listb)


