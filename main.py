import sys
import os

from pytexcount.parser import Parser
from pytexcount.visit_tree import PrintTreeStructure

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception('must have one argument')

    with open(sys.argv[1]) as f:
        tree = Parser(f.read()).parse()
        PrintTreeStructure()(tree)
