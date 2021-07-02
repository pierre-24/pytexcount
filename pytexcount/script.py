import argparse
import sys
from typing import List

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

MACRO_AS_WORDS = [
    'TeX',
    'LaTeX'
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
        '-i', '--include-macros', type=make_list, help='colon-separated list of macro args to include', default='')
    parser.add_argument(
        '-e', '--exclude-env', type=make_list, help='colon-separated list of environments to exclude', default='')
    parser.add_argument(
        '-w', '--words', type=make_list, help='colon-separated list of macros that count as word', default='')

    parser.add_argument(
        '-s', '--show', help='Show the list of excluded environments and included macro args', action='store_true')

    return parser


def show_list(title: str, lst: List[str]):
    print(title, end='')
    for i, element in enumerate(lst):
        if i != 0:
            print(', ', end='')
        if i % 5 == 0:
            print('\n  ', end='')

        print(element, end='')

    print()


def main():
    args = get_arguments_parser().parse_args()

    excluded_env = EXCLUDE_ENV + args.exclude_env
    included_macros = INCLUDE_MACRO + args.include_macros
    macro_as_words = MACRO_AS_WORDS + args.words

    if args.show:
        show_list('Excluded environments:', excluded_env)
        show_list('Include args of:', included_macros)
        show_list('Words:', macro_as_words)
        return

    try:
        tree = Parser(args.infile.read()).parse()
    except ParserSyntaxError as e:
        raise Exception('error while parsing: {}'.format(e))

    print(WordCounter(excluded_env, included_macros, macro_as_words)(tree))


if __name__ == '__main__':
    main()
