from typing import List, Iterator, Union
from enum import Enum, unique


@unique
class TokenType(Enum):
    BACKSLASH = '\\'
    LCBRACE = '{'
    RCBRACE = '}'
    LSBRACE = '['
    RSBRACE = ']',
    PERCENT = '%',
    SPACE = 'SPC',
    NL = 'NLW'
    EOS = '\0',
    CHAR = 'CHR'
    DOLLAR = '$'


SYMBOL_TR = {
    '\\': TokenType.BACKSLASH,
    '{': TokenType.LCBRACE,
    '}': TokenType.RCBRACE,
    '[': TokenType.LSBRACE,
    ']': TokenType.RSBRACE,
    '%': TokenType.PERCENT,
    '$': TokenType.DOLLAR,
    ' ': TokenType.SPACE,
    '\t': TokenType.SPACE,
    '\n': TokenType.NL
}


class Token:
    def __init__(self, typ_: TokenType, value: str, position: int = -1):
        self.type = typ_
        self.value = value
        self.position = position

    def __repr__(self):
        return 'Token({},{}{})'.format(
            self.type,
            self.value,
            '' if self.position < 0 else ', {}'.format(self.position)
        )


class Lexer:
    def __init__(self, inp):
        self.input = inp
        self.position = -1
        self.current_char = None

        self.next()

    def next(self):
        """Go to next token
        """

        self.position += 1

        if self.position >= len(self.input):
            self.current_char = '\0'
        else:
            self.current_char = self.input[self.position]

    def tokenize(self) -> Iterator[Token]:
        while self.current_char != '\0':
            if self.current_char in SYMBOL_TR:
                yield Token(SYMBOL_TR[self.current_char], self.current_char, self.position)
            else:
                yield Token(TokenType.CHAR, self.current_char, self.position)
            self.next()

        yield Token(TokenType.EOS, '\0', self.position)


class ParserNode:
    pass


class NodeWithChildren(ParserNode):
    def __init__(self, children: List[ParserNode]):
        self.children = children


class TeXDocument(NodeWithChildren):
    """First node type"""
    pass


class Text(ParserNode):
    """Pure text node, with no Environement/Macro in it"""

    def __init__(self, text: str):
        self.text = text


class Argument(NodeWithChildren):
    """Argument of a macro or an environment, may be optional or not"""
    def __init__(self, children: List[ParserNode], optional: bool = False):
        super().__init__(children)

        self.optional = optional


class Environment(NodeWithChildren):
    """Environment, defined as ``\\begin{name}[optarg1]{arg1} (...) \\end{name}``"""
    def __init__(self, name: str, arguments: List[Argument], children: List[ParserNode]):
        super().__init__(children)

        self.name = name
        self.arguments = arguments


class Macro(ParserNode):
    """Macro, defined as ``\\name[optarg1]{arg1}{arg2}``"""
    def __init__(self, name: str, arguments: List[Argument]):
        self.name = name
        self.arguments = arguments


class EscapingSequence(ParserNode):
    """One letter escaping sequence of the form ``\\x``, where ``x`` is a special character"""
    def __init__(self, to_escape: str):
        self.to_escape = to_escape


class MathEnvironment(NodeWithChildren):
    """Math ``$x$`` env
    """

    def __init__(self, children: List[ParserNode], double: bool = False):
        super().__init__(children)
        self.double = double


class ParserSyntaxError(Exception):
    pass


class Parser:
    def __init__(self, inp: str):
        self.lexer = Lexer(inp)
        self.tokenizer = self.lexer.tokenize()
        self.current_token: Token = None

        self.next()

    def next(self):
        """Get next token"""

        try:
            self.current_token = next(self.tokenizer)
        except StopIteration:
            self.current_token = Token(TokenType.EOS, '\0')

    def eat(self, typ: TokenType):
        if self.current_token.type == typ:
            self.next()
        else:
            raise ParserSyntaxError('expected {}, got {}'.format(typ, self.current_token))

    def skip_empty(self):
        """Skip spaces, newlines and comments
        """

        while self.current_token.type in [TokenType.SPACE, TokenType.PERCENT, TokenType.NL]:
            if self.current_token.type == TokenType.PERCENT:
                self.comment()
            else:
                self.next()

    def parse(self) -> TeXDocument:
        return self.tex_document()

    def children(
            self,
            in_math: bool = False,
            in_argument: TokenType = None
    ) -> List[ParserNode]:
        """Get children, but handle all specific parent environment
        """

        children = []

        while self.current_token.type != TokenType.EOS:
            if self.current_token.type == TokenType.PERCENT:
                self.comment()
            elif self.current_token.type == TokenType.BACKSLASH:
                children.append(self.escape_or_macro())
            elif self.current_token.type == TokenType.DOLLAR:
                if not in_math:
                    children.append(self.math_environment())
                else:  # if in math, it means the end
                    break
            else:
                children.append(self.text(extra_skip=in_argument))
                if in_argument is not None and self.current_token.type == in_argument:
                    break

        return children

    def tex_document(self) -> TeXDocument:
        """Get a document"""

        children = self.children()

        self.eat(TokenType.EOS)
        return TeXDocument(children)

    def comment(self):
        """Skip comment
        """

        self.eat(TokenType.PERCENT)
        while self.current_token.type not in [TokenType.NL, TokenType.EOS]:
            self.next()

    def escape_or_macro(self) -> Union[Macro, Environment, EscapingSequence]:
        """After a BACKSLASH could be either an escaping sequence,
        a macro or an environment (depending if its ``\\begin`` or not)
        """

        self.eat(TokenType.BACKSLASH)

        name = ''

        while self.current_token.type == TokenType.CHAR:
            if not self.current_token.value.isalnum():  # only alphanumeric stuffs in macro names
                break
            name += self.current_token.value
            self.next()

        if name == '':  # that's escaping
            val = self.current_token.value
            self.next()
            return EscapingSequence(val)
        else:  # macro, then
            arguments = self.arguments()
            return Macro(name, arguments)

    def arguments(self) -> List[Argument]:
        """Get the arguments, either optional (``[optarg]``) or not (``{arg}``)
        """

        self.skip_empty()
        arguments = []
        while self.current_token.type in [TokenType.LCBRACE, TokenType.LSBRACE]:
            arguments.append(self.argument())
            self.skip_empty()

        return arguments

    def argument(self) -> Argument:
        """Get argument"""

        if self.current_token.type not in [TokenType.LCBRACE, TokenType.LSBRACE]:
            raise ParserSyntaxError('not an argument, got {}'.format(self.current_token))

        optional = self.current_token.type == TokenType.LSBRACE
        opposite = {
            TokenType.LSBRACE: TokenType.RSBRACE,
            TokenType.LCBRACE: TokenType.RCBRACE}[self.current_token.type]
        self.next()

        children = self.children(in_argument=opposite)

        self.eat(opposite)
        return Argument(children, optional)

    def text(self, extra_skip: TokenType = None) -> Text:
        """Pure text, without env or macro.
        """

        opposite = None
        depth = 0 if extra_skip is None else 1

        if extra_skip:
            opposite = {
                TokenType.RSBRACE: TokenType.LSBRACE,
                TokenType.RCBRACE: TokenType.LCBRACE}[extra_skip]

        text = ''
        while self.current_token.type not in [TokenType.BACKSLASH, TokenType.EOS, TokenType.DOLLAR]:
            if self.current_token.type == TokenType.PERCENT:
                self.comment()
            elif self.current_token.type == opposite:
                depth += 1
            elif self.current_token.type == extra_skip:
                depth -= 1
                if depth == 0:
                    break

            text += self.current_token.value
            self.next()

        return Text(text)

    def math_environment(self) -> MathEnvironment:
        self.eat(TokenType.DOLLAR)
        double = False
        if self.current_token.type == TokenType.DOLLAR:
            double = True
            self.eat(TokenType.DOLLAR)

        children = self.children(in_math=True)

        self.eat(TokenType.DOLLAR)
        if double:
            self.eat(TokenType.DOLLAR)

        return MathEnvironment(children, double=double)


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