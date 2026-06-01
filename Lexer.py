from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    VAR = "var"
    FUNC = "func"
    IFUNC = "ifunc"

    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"

    IDENTIFIER = "identifier"

    NUMBER = "number"
    STRING = "string"
    CHAR = "char"

    PLUS = "+"
    MINUS = "-"
    MUL = "*"

    ASSIGN = "="

    EQ = "=="
    NE = "!="

    LT = "<"
    LE = "<="

    GR = ">"
    GE = ">="

    LBRACKET = "("
    RBRACKET = ")"

    LFIG = "{"
    RFIG = "}"

    COMMA = ","
    SEMICOLON = ";"

    IN = "@"
    OUT = "%"
    READ = "&"
    EI = "$"
    DI = "!$"

    EOF = "EOF"

KEYWORDS = {
    "var": TokenType.VAR,
    "func": TokenType.FUNC,
    "ifunc": TokenType.IFUNC,

    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,

    "return": TokenType.RETURN
}

OPERATORS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MUL,
    "=": TokenType.ASSIGN,

    "(": TokenType.LBRACKET,
    ")": TokenType.RBRACKET,
    "{": TokenType.LFIG,
    "}": TokenType.RFIG,

    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,

    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<": TokenType.LT,
    "<=": TokenType.LE,
    ">": TokenType.GR,
    ">=": TokenType.GE,

    "@": TokenType.IN,
    "%": TokenType.OUT,
    "&": TokenType.READ,
    "!$": TokenType.DI,
    "$": TokenType.EI
}

@dataclass
class Token:
    type: TokenType
    value: str | int | None
    line: int

class Lexer:
    source: str
    pos: int
    line: int

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 0

    def current(self):
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def advance(self):
        if self.current() == "\n":
            self.line += 1
        self.pos += 1

    def skip_spaces(self):
        while self.current() is not None and self.current().isspace():
            self.advance()

    def read_number(self):
        value = ""
        while self.current() is not None and self.current().isdigit():
            value += self.current()
            self.advance()

        return Token(TokenType.NUMBER, int(value), self.line)

    def read_identifier(self):
        value = ""
        while self.current() is not None and (self.current().isalnum() or self.current() == "_"):
            value += self.current()
            self.advance()
        token_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, self.line)

    def read_string(self):
        self.advance()
        value = ""
        while self.current() != "\"":
            if self.current() is None:
                raise SyntaxError("Unterminated string")
            value += self.current()
            self.advance()
        self.advance()

        return Token(TokenType.STRING, value, self.line)

    def read_char(self):
        self.advance()

        if self.current() is None:
            raise SyntaxError("Bad char")

        value = self.current()

        if self.current() == "\\":
            self.advance()
            if self.current() == "n":
                value = '\n'
            else:
                raise SyntaxError("Bad char")

        self.advance()

        if self.current() != "'":
            raise SyntaxError("Bad char")

        self.advance()

        return Token(
            TokenType.CHAR,
            value,
            self.line
        )

    def read_operator(self):
        c = self.current()

        if c in "<>!=":
            self.advance()

            if self.current() == "=":
                op = c + "="
                self.advance()
                return Token(OPERATORS[op], op, self.line)
            if self.current() == "$":
                op = c + "$"
                self.advance()
                return Token(OPERATORS[op], op, self.line)
            if c == "!":
                raise SyntaxError("Expected '=' after '!'")

            return Token(OPERATORS[c], c, self.line)

        self.advance()

        return Token(OPERATORS[c], c, self.line)

    def tokenize(self):
        tokens = []

        while self.current() is not None:
            self.skip_spaces()

            c = self.current()

            if c is None:
                break

            if c.isdigit():
                tokens.append(self.read_number())
                continue

            if c.isalpha() or c == "_":
                tokens.append(self.read_identifier())
                continue

            if c == "\"":
                tokens.append(self.read_string())
                continue

            if c =="'":
                tokens.append(self.read_char())
                continue
            if c in "=+-*<>,;(){}!@%&$":
                tokens.append(self.read_operator())
                continue

            raise SyntaxError(f"Unexpected character '{c}'  at line {self.line}")

        tokens.append(Token(TokenType.EOF, None, self.line))

        return tokens