#
# Tobias Rubel | rubelato@reed.edu
# Reed CompBio
#
# This script just parses the yaml config files


import yaml
import os
import sys


def main(argv):
    f = argv[1]
    with open(f,'r') as g:
        print(yaml.safe_load(g))



if __name__ == "__main__":
    main(sys.argv)
