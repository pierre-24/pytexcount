from pytexcount import parser


class NodeVisitor(object):
    """Implementation of the visitor pattern.
    Expect ``visit_[type](node)`` functions, where ``[type]`` is the type of the node, **lowercased**.
    """

    def visit(self, node, *args, **kwargs):
        method_name = 'visit_' + type(node).__name__.lower()
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        raise Exception('No visit_{} method'.format(type(node).__name__.lower()))


class PrintTreeStructure(NodeVisitor):
    def __call__(self, node: parser.ParserNode):
        self.visit(node, depth=0)

    @staticmethod
    def indent(depth: int, spacer: str = '|  '):
        print(spacer * depth, end='')

    def visit_texdocument(self, node: parser.TeXDocument, depth):
        PrintTreeStructure.indent(depth)
        print('+ TexDocument::')

        for child in node.children:
            self.visit(child, depth + 1)

    def visit_text(self, node: parser.Text, depth):
        PrintTreeStructure.indent(depth)
        print('+ Text: `{}`'.format(node.text))

    def visit_macro(self, node: parser.Macro, depth):
        PrintTreeStructure.indent(depth)
        print('+ Macro ({})::'.format(node.name))
        for argument in node.arguments:
            self.visit(argument, depth + 1)

    def visit_argument(self, node: parser.Argument, depth):
        PrintTreeStructure.indent(depth)
        print('+ Argument ({})::'.format('optional' if node.optional else 'mandatory'))
        for child in node.children:
            self.visit(child, depth + 1)

    def visit_environment(self, node: parser.Environment, depth):
        PrintTreeStructure.indent(depth)
        print('+ Environment ({})::'.format(node.name))
        for argument in node.arguments:
            self.visit(argument, depth + 1)
        for child in node.children:
            self.visit(child, depth + 1)

    def visit_escapingsequence(self, node: parser.EscapingSequence, depth):
        PrintTreeStructure.indent(depth)
        print('+ Escaping sequence ({})::'.format(node.to_escape))

    def visit_mathdollarenv(self, node: parser.MathDollarEnv, depth):
        PrintTreeStructure.indent(depth)
        print('+ MathEnvironment ({})::'.format('$$' if node.double else '$'))
        for child in node.children:
            self.visit(child, depth + 1)

    def visit_enclosed(self, node: parser.Enclosed, depth):
        PrintTreeStructure.indent(depth)
        print('+ Enclosing ({})::'.format(node.opening))
        for child in node.children:
            self.visit(child, depth + 1)
