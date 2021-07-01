"""Count the number of words in a TeX document, but cleverly
"""

import argparse
import sys

from pytexcount.parser import Parser, ParserSyntaxError
from pytexcount.count import WordCounter

__version__ = '0.1'
__author__ = 'Pierre Beaujean'
__maintainer__ = 'Pierre Beaujean'
__email__ = 'pierre.beaujean@unamur.be'
__status__ = 'Development'


INCLUDE_MACRO = [
    # text
    'textbf',
    'textit',
    'emph',

    # floats
    'caption',

    # title levels
    'section',
    'subsection',
    'subsubsection',
    'paragraph',
    'subparagraph'
]

EXCLUDE_ENV = [
    'equation',
    'equation*',
    'align',
    'align*'
]


def make_list(inp):
    return inp.split(',')


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    parser.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='TeX source')

    parser.add_argument(
        '-i', '--include-macro', type=make_list, help='colon-separated list of macro to include', default='')
    parser.add_argument(
        '-e', '--exclude-env', type=make_list, help='colon-separated list of environments to exclude', default='')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    try:
        tree = Parser(args.infile.read()).parse()
    except ParserSyntaxError as e:
        raise Exception('error while parsing: {}'.format(e))

    print(WordCounter(EXCLUDE_ENV + args.exclude_env, INCLUDE_MACRO + args.include_macro)(tree))


if __name__ == '__main__':
    main()