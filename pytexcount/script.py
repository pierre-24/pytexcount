import argparse
import sys

import pytexcount
from pytexcount.parser import Parser, ParserSyntaxError
from pytexcount.count import WordCounter


INCLUDE_MACRO = [
    # text
    'textbf',
    'textit',
    'texttt',
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
    if inp == '':
        return []
    else:
        return inp.split(',')


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=pytexcount.__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + pytexcount.__version__)

    parser.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='TeX source')

    parser.add_argument(
        '-i', '--include-macros', type=make_list, help='colon-separated list of macros to include', default='')
    parser.add_argument(
        '-e', '--exclude-env', type=make_list, help='colon-separated list of environments to exclude', default='')

    parser.add_argument(
        '-s', '--show', help='Show the list of exluced environments and included macros', action='store_true')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    excluded_env = EXCLUDE_ENV + args.exclude_env
    included_macros = INCLUDE_MACRO + args.include_macros

    if args.show:
        print('Excluded env:', ', '.join(excluded_env))
        print('Included macros:', ', '.join(included_macros))
        return

    try:
        tree = Parser(args.infile.read()).parse()
    except ParserSyntaxError as e:
        raise Exception('error while parsing: {}'.format(e))

    print(WordCounter(excluded_env, included_macros)(tree))


if __name__ == '__main__':
    main()
