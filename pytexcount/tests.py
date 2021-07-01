import unittest

from pytexcount.parser import Lexer, Token as T, TokenType as TT, Parser
from pytexcount.print_tree import PrintTreeStructure


class LexerTestCase(unittest.TestCase):

    def test_lexer_base(self):
        expected = [
            T(TT.CHAR, 'a'),
            T(TT.SPACE, ' '),
            T(TT.BACKSLASH, '\\'),
            T(TT.CHAR, 't'),
            T(TT.LCBRACE, '{'),
            T(TT.CHAR, 'x'),
            T(TT.RCBRACE, '}'),
            T(TT.EOS, '\0')
        ]

        for i, token in enumerate(Lexer('a \\t{x}').tokenize()):
            self.assertEqual(token.type, expected[i].type)
            self.assertEqual(token.value, expected[i].value)


class ParserTestCase(unittest.TestCase):

    def test_parser_simple(self):
        text = """\\begin{test}content\\end{test}"""
        tree = Parser(text).parse()
        PrintTreeStructure()(tree)
