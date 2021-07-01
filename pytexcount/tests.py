import unittest

import pytexcount.parser as P
from pytexcount.parser import Lexer, Token as T, TokenType as TT, Parser
from pytexcount.visit_tree import PrintTreeStructure


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

    def test_parser_text(self):
        text = "xy"
        tree = Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text)

    def test_parser_text_with_comment(self):
        text = "xy %a"
        tree = Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text[:text.find('%')])

    def test_parser_enclosed(self):
        bef_text = 'x'
        enclosed_text = 'a'
        aft_text = 'y'

        text = "{}[{}]{}".format(bef_text, enclosed_text, aft_text)
        tree = Parser(text).parse()

        self.assertEqual(len(tree.children), 3)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, bef_text)

        self.assertIsInstance(tree.children[1], P.Enclosed)
        self.assertEqual(tree.children[1].opening, TT.LSBRACE)
        self.assertEqual(tree.children[1].closing(), TT.RSBRACE)
        self.assertEqual(tree.children[1].children[0].text, enclosed_text)

        self.assertIsInstance(tree.children[2], P.Text)
        self.assertEqual(tree.children[2].text, aft_text)

    def test_parser_macro(self):
        name = 'test'
        optarg = 'x'
        mandarg = 'y'
        text = "\\{}[{}]{{{}}}".format(name, optarg, mandarg)
        tree = Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Macro)

        macro: P.Macro = tree.children[0]
        self.assertEqual(macro.name, name)
        self.assertEqual(len(macro.arguments), 2)
        self.assertEqual(macro.arguments[0].children[0].text, optarg)
        self.assertTrue(macro.arguments[0].optional)
        self.assertEqual(macro.arguments[1].children[0].text, mandarg)
        self.assertFalse(macro.arguments[1].optional)

    def test_parser_math(self):
        textpart = 'a'
        mathpart = 'x'
        text = "{}${}$".format(textpart, mathpart)
        tree = Parser(text).parse()

        self.assertEqual(len(tree.children), 2)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, textpart)

        self.assertIsInstance(tree.children[1], P.MathDollarEnv)
        mathenv = tree.children[1]
        self.assertEqual(mathenv.children[0].text, mathpart)

    def test_parser_env(self):
        text = """x \\begin{test}content\\end{test}"""
        tree = Parser(text).parse()
        PrintTreeStructure()(tree)
