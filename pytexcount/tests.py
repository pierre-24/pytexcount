import unittest

import pytexcount.parser as P
from pytexcount.count import WordCounter
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

    def parse(self, text):
        return P.Parser(text).parse()

    def test_parser_text(self):
        text = 'xy'
        tree = self.parse(text)

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text)

    def test_parser_text_with_comment(self):
        text = 'xy %a'
        tree = self.parse(text)

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, text[:text.find('%')])

    def test_parser_enclosed(self):
        bef_text = 'x'
        enclosed_text = 'a'
        aft_text = 'y'

        text = '{}[{}]{}'.format(bef_text, enclosed_text, aft_text)
        tree = self.parse(text)

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
        text = '\\{}[{}]{{{}}}'.format(name, optarg, mandarg)
        tree = self.parse(text)

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Macro)

        macro: P.Macro = tree.children[0]
        self.assertEqual(macro.name, name)
        self.assertEqual(len(macro.arguments), 2)
        self.assertEqual(macro.arguments[0].children[0].text, optarg)
        self.assertTrue(macro.arguments[0].optional)
        self.assertEqual(macro.arguments[1].children[0].text, mandarg)
        self.assertFalse(macro.arguments[1].optional)

    def test_macro_name(self):
        def mc(t) -> P.Macro:
            return P.Parser(t).escape_or_macro()

        self.assertEqual(mc('\\test').name, 'test')
        self.assertEqual(mc('\\test2').name, 'test2')
        self.assertEqual(mc('\\test*').name, 'test*')
        self.assertEqual(mc('\\x@test').name, 'x@test')
        self.assertEqual(mc('\\test_2').name, 'test')
        self.assertEqual(mc('\\test^2').name, 'test')

    def test_parser_math(self):
        textpart = 'a'
        mathpart = 'x'
        text = '{}${}$'.format(textpart, mathpart)
        tree = self.parse(text)

        self.assertEqual(len(tree.children), 2)
        self.assertIsInstance(tree.children[0], P.Text)
        self.assertEqual(tree.children[0].text, textpart)

        self.assertIsInstance(tree.children[1], P.MathDollarEnv)
        mathenv = tree.children[1]
        self.assertEqual(mathenv.children[0].text, mathpart)

    def test_parser_env(self):
        name = 'test'
        content = 'tmp'
        text = '\\begin{{{name}}}{ctn}\\end{{{name}}}'.format(name=name, ctn=content)
        tree = self.parse(text)

        self.assertEqual(len(tree.children), 1)
        self.assertIsInstance(tree.children[0], P.Environment)
        self.assertEqual(tree.children[0].name, name)

        self.assertEqual(tree.children[0].children[0].text, content)

    def test_parser_env_in_env(self):
        """Environment in environment (with the same name)
        """

        text = 'a\\begin{test}b\\begin{test}c\\end{test}d\\end{test}e'
        tree = self.parse(text)

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

    def test_unary(self):
        tree = self.parse('\\alpha_{xy} z')
        PrintTreeStructure()(tree)


class WordCountTestCase(unittest.TestCase):

    def count(self, text, exclude_env=None, include_macro=None, macro_as_word=None):
        tree = P.Parser(text).parse()
        return WordCounter(exclude_env, include_macro, macro_as_word)(tree)

    def test_text(self):
        self.assertEqual(self.count('this is a test'), 4)
        self.assertEqual(self.count('this is the 2nd test'), 5)

    def test_enclosed(self):
        self.assertEqual(self.count('a [b] c'), 3)

    def test_macro(self):
        self.assertEqual(self.count('\\test{x}{y}'), 0)
        self.assertEqual(self.count('\\test{x}{y}', include_macro=['test']), 2)

    def test_macro_as_word(self):
        self.assertEqual(self.count('a \\test'), 1)
        self.assertEqual(self.count('a \\test', macro_as_word=['test']), 2)

    def test_environment(self):
        self.assertEqual(self.count('\\begin{test}two words\\end{test}'), 2)
        self.assertEqual(self.count('\\begin{test}two words\\end{test}', exclude_env=['test']), 0)

    def test_tabular(self):
        self.assertEqual(self.count('\\begin{tabular}a & b\\end{tabular}'), 2)

    def test_unary(self):
        self.assertEqual(self.count('\\alpha_{xx}', macro_as_word=['alpha']), 1)
