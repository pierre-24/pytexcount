from typing import List, Iterator, Union
from enum import Enum, unique


@unique
class TokenType(Enum):
    BACKSLASH = '\\'
    LCBRACE = '{'
    RCBRACE = '}'
    LSBRACE = '['
    RSBRACE = ']'
    PERCENT = '%'
    UP = '^'
    DOWN = '_'
    AMPERSAND = '&'
    SPACE = 'SPC'
    NL = 'NLW'
    EOS = '\0'
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
    '^': TokenType.UP,
    '_': TokenType.DOWN,
    '&': TokenType.AMPERSAND,
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
    """Pure text node, with no Environment/Macro in it"""

    def __init__(self, text: str):
        self.text = text


class Enclosed(NodeWithChildren):
    """Node enclosed with either [R|C]BRACES"""

    def __init__(self, opening: TokenType, children: List[ParserNode]):
        super().__init__(children)

        if opening not in [TokenType.LCBRACE, TokenType.LSBRACE]:
            raise ParserSyntaxError('incorrect TokenType for Enclosed, got {}'.format(opening))

        self.opening = opening

    def closing(self):
        return TokenType.RCBRACE if self.opening == TokenType.LCBRACE else TokenType.RSBRACE


class Argument(Enclosed):
    """Argument of a macro or an environment, may be optional or not"""

    def __init__(self, children: List[ParserNode], optional: bool = False):
        super().__init__(opening=TokenType.LSBRACE if optional else TokenType.LCBRACE, children=children)
        self.optional = optional


class UnaryOperator(NodeWithChildren):
    """``_`` and ``^``"""

    def __init__(self, op: TokenType, children: List[ParserNode]):
        super().__init__(children)

        if op not in [TokenType.DOWN, TokenType.UP]:
            raise ParserSyntaxError('incorrect TokenType for UnaryOperator, got {}'.format(op))

        self.operator = op


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


class Separator(ParserNode):
    """Just &"""
    pass


class MathDollarEnv(NodeWithChildren):
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

    def _next(self):
        """Get next token"""

        try:
            self.current_token = next(self.tokenizer)
        except StopIteration:
            self.current_token = Token(TokenType.EOS, '\0')

    def next(self):
        """Get next token, but skip comment"""

        self._next()

        if self.current_token.type == TokenType.PERCENT:
            self.next()
            while self.current_token.type not in [TokenType.NL, TokenType.EOS]:
                self._next()

    def eat(self, typ: TokenType):
        if self.current_token.type == typ:
            self.next()
        else:
            raise ParserSyntaxError('expected {}, got {}'.format(typ, self.current_token))

    def skip_empty(self):
        """Skip spaces, newlines and comments
        """

        while self.current_token.type in [TokenType.SPACE, TokenType.NL]:
            self.next()

    def parse(self) -> TeXDocument:
        return self.tex_document()

    @staticmethod
    def is_valid__for_env(macro: Macro, name: str = 'begin') -> bool:
        if type(macro) is not Macro:
            return False
        if macro.name != name:
            return False
        if len(macro.arguments) != 1:
            return False
        if len(macro.arguments[0].children) != 1:
            return False
        if type(macro.arguments[0].children[0]) is not Text:
            return False

        return True

    def child(self) \
            -> Union[Text, Macro, MathDollarEnv, Enclosed, EscapingSequence, UnaryOperator, Environment, Separator]:
        if self.current_token.type == TokenType.BACKSLASH:
            macro = self.escape_or_macro()
            if Parser.is_valid__for_env(macro):
                return self.environment(macro)
            else:
                return macro
        elif self.current_token.type == TokenType.DOLLAR:
            return self.math_environment()
        elif self.current_token.type in [TokenType.LCBRACE, TokenType.LSBRACE]:
            return self.enclosed()
        elif self.current_token.type in [TokenType.UP, TokenType.DOWN]:
            return self.unary_operator()
        elif self.current_token.type == TokenType.AMPERSAND:
            self.next()
            return Separator()
        else:
            return self.text()

    def tex_document(self) -> TeXDocument:
        """Get a document"""

        children = []
        while self.current_token.type != TokenType.EOS:
            children.append(self.child())

        self.eat(TokenType.EOS)
        return TeXDocument(children)

    def escape_or_macro(self) -> Union[Macro, EscapingSequence]:
        """After a BACKSLASH could be either an escaping sequence or a macro
        """

        self.eat(TokenType.BACKSLASH)

        name = ''

        while self.current_token.type == TokenType.CHAR:
            if not self.current_token.value.isalnum() and self.current_token.value not in ['*', '@']:
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
            enclosed = self.enclosed()
            arguments.append(Argument(enclosed.children, enclosed.opening == TokenType.LSBRACE))
            self.skip_empty()

        return arguments

    def enclosed(self) -> Enclosed:
        """Get enclosed
        """

        if self.current_token.type not in [TokenType.LCBRACE, TokenType.LSBRACE]:
            raise ParserSyntaxError('not an enclosed, got {}'.format(self.current_token))

        opening = self.current_token.type
        opposite = {
            TokenType.LSBRACE: TokenType.RSBRACE,
            TokenType.LCBRACE: TokenType.RCBRACE}[self.current_token.type]

        self.next()

        children = []
        while self.current_token.type != TokenType.EOS:
            if self.current_token.type == opposite:
                break

            children.append(self.child())

        self.eat(opposite)
        return Enclosed(opening, children)

    def text(self) -> Text:
        """Pure text, without env or macro.
        """

        text = ''
        while self.current_token.type in [
            TokenType.CHAR, TokenType.SPACE, TokenType.NL
        ]:

            text += self.current_token.value
            self.next()

        return Text(text)

    def math_environment(self) -> MathDollarEnv:
        self.eat(TokenType.DOLLAR)
        double = False
        if self.current_token.type == TokenType.DOLLAR:
            double = True
            self.eat(TokenType.DOLLAR)

        children = []
        while self.current_token.type != TokenType.EOS:
            if self.current_token.type == TokenType.DOLLAR:
                break

            children.append(self.child())

        self.eat(TokenType.DOLLAR)
        if double:
            self.eat(TokenType.DOLLAR)

        return MathDollarEnv(children, double=double)

    def environment(self, macro_begin: Macro) -> Environment:
        def get_name(m: Macro):
            return m.arguments[0].children[0].text.strip()

        name = get_name(macro_begin)  # assume that `is_valid_for_env` is True!
        arguments = macro_begin.arguments[1:]

        children = []
        while self.current_token.type != TokenType.EOS:
            child = self.child()
            if type(child) is Macro and Parser.is_valid__for_env(child, 'end') and get_name(child) == name:
                return Environment(name, arguments, children)
            else:
                children.append(child)

        raise ParserSyntaxError('EOS while parsing environment {}'.format(name))

    def unary_operator(self) -> UnaryOperator:
        """Get unary operator"""

        if self.current_token.type not in [TokenType.UP, TokenType.DOWN]:
            raise ParserSyntaxError('not an unary, got {}'.format(self.current_token))

        operator = self.current_token.type
        self.next()

        children = []
        if self.current_token.type == TokenType.LCBRACE:
            self.next()

            while self.current_token.type != TokenType.EOS:
                if self.current_token.type == TokenType.RCBRACE:
                    break

                children.append(self.child())

            self.eat(TokenType.RCBRACE)

        elif self.current_token.type == TokenType.CHAR:  # normally, it can only be CHAR?!?
            children.append(Text(self.current_token.value))
            self.next()

        return UnaryOperator(operator, children)
