# template for CLI for now. Should move to a src/ folder when it becomes something.
import argparse

## global variables of supported algorithms, etc.
ALGS = ['oi2','pathlinker']
VIZ = ['cytoscape','graphspace','networkx']

def main():
    ## stub
    return

# from https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
def print_full_help(parser):
    print(parser.format_help())

    # retrieve subparsers from parser
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
    # there will probably only be one subparser_action,
    # but better safe than sorry
    for subparsers_action in subparsers_actions:
        # get all subparsers and print help
        for choice, subparser in subparsers_action.choices.items():
            print('--'*10)
            print("Arguments for '{}'".format(choice))
            print(subparser.format_help())
    return

## argument parser for CLI.
## throw errors if improper arguments are passed.
def parse_args():
    parser = argparse.ArgumentParser("<ADD DESCRIPTION>")

    ## Optional arguments shared by all subparsers.
    parser.add_argument("--config",metavar="STR",default=None,help="Configuration file.  Any command-line inputs overwrite those specificed in the config file.")
    parser.add_argument("-o","--outdir",metavar="STR",default="out/",help="Output directory. Default: out/")
    parser.add_argument("--full-help",action="store_true",help="Print the full help message, including all subparsers.")

    # each action is a subparser with its own optional arguments.
    subparsers = parser.add_subparsers() # can add description here.

    subp0 = subparsers.add_parser("prepare-input",help="Prepare files for pathway reconstruction.")
    subp0.add_argument("--network",metavar="STR",default=None,help="Network file.")
    subp0.add_argument("--sources",metavar="STR",default=None,help="File of source nodes.")
    subp0.add_argument("--targets",metavar="STR",default=None,help="File of target nodes.")
    subp0.add_argument("--nodes",metavar="STR",default=None,help="File of nodes.")

    subp1 = subparsers.add_parser("reconstruct",help="Reconstruct pathways.")
    subp1.add_argument("--alg",metavar="STR",nargs="+",help="Algorithms. Possible options are 'all' "+" ".join(["'%s'"%a for a in ALGS]))
    subp1.add_argument("--k",metavar="INT",default=100,help="pathlinker arg: Number of paths for PathLinker to return. Default 100.")
    subp1.add_argument('--rho',type=int,metavar='INT',default=5,help="oi2: terminal prize. Default 5.")
    subp1.add_argument('--b',type=int,metavar='INT',default=1,help="oi2: edge reliability. Default 1.")
    subp1.add_argument('--omega',type=int,metavar='INT',default=5,help="oi2: dummy edge weight. Default 5.")
    subp1.add_argument('-g',type=int,metavar='INT',default=3,help="oi2: degree penalty. Default 3.")

    subp2 = subparsers.add_parser("parse-output",help="Parse reconstruction outputs.")

    subp3 = subparsers.add_parser("augment",help="Augment reconstruction outputs.")

    subp4 = subparsers.add_parser("ensemble",help="Ensemble reconstruction outputs.")

    subp5 = subparsers.add_parser("parameter-advise",help="Advise reconstruction parameters.")

    subp6 = subparsers.add_parser("evaluate",help="Evaluate reconstruction outputs.")
    subp6.add_argument("--ground-truth-edges",metavar="STR",default=None,help="Gound truth edges (subset of network file).")
    subp6.add_argument("--ground-truth-nodes",metavar="STR",default=None,help="Gound truth nodes (subset of nodes in network file).")
    subp6.add_argument("--pr",action="store_true",help="Compute precision and recall.")

    subp7 = subparsers.add_parser("visualize",help="Visualize reconstruction outputs.")
    subp7.add_argument('--viz',metavar="STR",nargs="+",help="Vizualization platforms. Possible options are 'all' "+" ".join(["'%s'"%a for a in VIZ]))

    args = parser.parse_args()
    if args.full_help:
        print_full_help(parser)

    return args

if __name__ == "__main__":
    args = parse_args()
    main()
