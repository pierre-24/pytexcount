import unittest

import pytexcount.parser as P
from pytexcount.visit_tree import PrintTreeStructure


class LexerTestCase(unittest.TestCase):

    def test_lexer_base(self):
        expected = [
            P.Token(P.TokenType.CHAR, 'a'),
            P.Token(P.TokenType.SPACE, ' '),
            P.Token(P.TokenType.BACKSLASH, '\\'),
            P.Token(P.TokenType.CHAR, 't'),
            P.Token(P.TokenType.LCBRACE, '{'),
            P.Token(P.TokenType.CHAR, 'x'),
            P.Token(P.TokenType.RCBRACE, '}'),
            P.Token(P.TokenType.EOS, '\0')
        ]

        for i, token in enumerate(P.Lexer('a \\t{x}').tokenize()):
            self.assertEqual(token.type, expected[i].type)
            self.assertEqual(token.value, expected[i].value)


class ParserTestCase(unittest.TestCase):

    def test_parser_text(self):
        text = "xy"
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text)

    def test_parser_text_with_comment(self):
        text = "xy %a"
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text[:text.find('%')])

    def test_parser_enclosed(self):
        bef_text = 'x'
        enclosed_text = 'a'
        aft_text = 'y'

        text = "{}[{}]{}".format(bef_text, enclosed_text, aft_text)
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 3)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, bef_text)

        self.assertIsInstance(tree.children[1], P.Enclosed)
        self.assertEqual(tree.children[1].opening, P.TokenType.LSBRACE)
        self.assertEqual(tree.children[1].closing(), P.TokenType.RSBRACE)
        self.assertEqual(tree.children[1].children[0].text, enclosed_text)

        self.assertIsInstance(tree.children[2], P.Text)
        self.assertEqual(tree.children[2].text, aft_text)

    def test_parser_macro(self):
        name = 'test'
        optarg = 'x'
        mandarg = 'y'
        text = "\\{}[{}]{{{}}}".format(name, optarg, mandarg)
        tree = P.Parser(text).parse()

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
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 2)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, textpart)

        self.assertIsInstance(tree.children[1], P.MathDollarEnv)
        mathenv = tree.children[1]
        self.assertEqual(mathenv.children[0].text, mathpart)

    def test_parser_env(self):
        name = 'test'
        content = 'tmp'
        text = "\\begin{{{name}}}{ctn}\\end{{{name}}}".format(name=name, ctn=content)
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Environment)
        self.assertEqual(tree.children[0].name, name)

        self.assertEqual(tree.children[0].children[0].text, content)

    def test_parser_env_in_env(self):
        """Environment in environment (with the same name)
        """

        text = """a\\begin{test}b\\begin{test}c\\end{test}d\\end{test}e"""
        tree = P.Parser(text).parse()

        self.assertEqual(len(tree.children), 3)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, 'a')
        self.assertIsInstance(tree.children[1], P.Environment)
        self.assertIsInstance(tree.children[2], P.Text)
        self.assertEqual(tree.children[2].text, 'e')

        env: P.Environment = tree.children[1]
        self.assertEqual(env.name, 'test')

        self.assertEqual(len(env.children), 3)
        self.assertIsInstance(env.children[0], P.Text)
        self.assertEqual(env.children[0].text, 'b')
        self.assertIsInstance(env.children[1], P.Environment)
        self.assertEqual(env.children[1].children[0].text, 'c')
        self.assertIsInstance(env.children[2], P.Text)
        self.assertEqual(env.children[2].text, 'd')

