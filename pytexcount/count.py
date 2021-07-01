from typing import List

from pytexcount import parser
from pytexcount.visit_tree import NodeVisitor


class WordCounter(NodeVisitor):
    def __init__(self, exclude_env: List[str], include_macro: List[str]):
        self.exclude_env = frozenset(exclude_env if exclude_env is not None else [])
        self.include_macro = frozenset(include_macro if include_macro is not None else [])

    def __call__(self, node: parser.ParserNode):
        return self.visit(node)

    def visit_texdocument(self, node: parser.TeXDocument):
        return sum(self.visit(child) for child in node.children)

    def visit_macro(self, node: parser.Macro):
        if node.name in self.include_macro:
            return sum(self.visit(arg) for arg in node.arguments)

        return 0

    def visit_environment(self, node: parser.Environment):
        if node.name not in self.exclude_env:
            return sum(self.visit(arg) for arg in node.children)

        return 0

    def visit_argument(self, node: parser.Argument):
        return sum(self.visit(arg) for arg in node.children)

    def visit_mathdollarenv(self, node: parser.MathDollarEnv):
        if not node.double:
            return sum(self.visit(arg) for arg in node.children)
        else:
            return 0

    def visit_enclosed(self, node: parser.Enclosed):
        return sum(self.visit(arg) for arg in node.children)

    def visit_escapesequence(self, node):
        return 0

    def visit_text(self, node: parser.Text):
        text = node.text

        if len(text) == 0:
            return 0
        else:
            nwords = 0
            in_word = text[0].isspace()

            for c in text:
                if c.isspace() and in_word:
                    in_word = False

                if not c.isspace() and not in_word:
                    in_word = True
                    nwords += 1

            return nwords