from Lexer import TokenType, Token


class Node:
    pass

class NumberNode(Node):
    def __init__(self, value):
        self.value = value

class StringNode(Node):
    def __init__(self, value):
        self.value = value

class CharNode(Node):
    def __init__(self, value):
        self.value = value

class IdentifierNode(Node):
    def __init__(self, name):
        self.name = name

class VarDeclNode(Node):
    def __init__(self, name, value=None):
        self.name = name
        self.value = value

class AssignNode(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ConditionNode(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class IfNode(Node):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileNode(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ReturnNode(Node):
    def __init__(self, value=None):
        self.value = value

class FunctionCallNode(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class FunctionNode(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class InterruptFunctionNode(Node):
    def __init__(self, port, body):
        self.port = port
        self.body = body

class ProgramNode(Node):
    def __init__(self, declarations):
        self.declarations = declarations

class BinaryOpNode(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class InNode(Node):
    def __init__(self):
        pass

class OutNode(Node):
    def __init__(self, value):
        self.value = value

class ReadNode(Node):
    def __init__(self, value):
        self.value = value

class EINode(Node):
    def __init__(self):
        pass

class DINode(Node):
    def __init__(self):
        pass

class Parser:
    tokens: list
    pos: int

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        self.pos += 1

    def match(self, token_type):
        if self.current().type == token_type:
            self.advance()
            return True

        return False

    def consume(self, token_type):
        token = self.current()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type}, got {token.type}"
            )

        self.advance()
        return token

    def parse_program(self):
        declarations = []
        while self.current().type != TokenType.EOF:
            declarations.append(
                self.parse_declaration()
            )

        return ProgramNode(declarations)

    def parse_declaration(self):

        token_type = self.current().type

        if token_type == TokenType.VAR:
            return self.parse_var_decl()

        if token_type == TokenType.FUNC:
            return self.parse_func_decl()

        if token_type == TokenType.IFUNC:
            return self.parse_ifunc_decl()

        return self.parse_statement()

    def parse_var_decl(self):
        self.consume(TokenType.VAR)
        name = self.consume(
            TokenType.IDENTIFIER
        ).value

        value = None
        if self.match(TokenType.ASSIGN):
            value = self.parse_expression()
        self.consume(TokenType.SEMICOLON)

        return VarDeclNode(name, value)

    def parse_block(self):
        self.consume(TokenType.LFIG)
        statements = []
        while self.current().type not in (
                TokenType.RFIG,
                TokenType.EOF
        ):
            if self.current().type == TokenType.EOF:
                raise SyntaxError("Expected '}'")
            statements.append(
                self.parse_statement()
            )

        self.consume(TokenType.RFIG)
        return statements

    def parse_func_decl(self):
        self.consume(TokenType.FUNC)
        name = self.consume(
            TokenType.IDENTIFIER
        ).value
        self.consume(TokenType.LBRACKET)
        params = []
        if self.current().type != TokenType.RBRACKET:
            params.append(
                self.consume(
                    TokenType.IDENTIFIER
                ).value
            )

            while self.current().type == TokenType.COMMA:
                self.advance()

                params.append(
                    self.consume(
                        TokenType.IDENTIFIER
                    ).value
                )

        self.consume(TokenType.RBRACKET)
        body = self.parse_block()
        return FunctionNode(name, params, body)

    def parse_ifunc_decl(self):
        self.consume(TokenType.IFUNC)
        self.consume(TokenType.IDENTIFIER)
        self.consume(TokenType.LBRACKET)

        port = self.consume(
            TokenType.NUMBER
        ).value

        self.consume(TokenType.RBRACKET)
        body = self.parse_block()
        return InterruptFunctionNode(port, body)

    def parse_statement(self):
        t = self.current().type
        if t == TokenType.VAR:
            return self.parse_var_decl()

        if t == TokenType.IF:
            return self.parse_if()

        if t == TokenType.WHILE:
            return self.parse_while()

        if t == TokenType.RETURN:
            return self.parse_return()

        if t == TokenType.IDENTIFIER:
            if self.pos + 1 >= len(self.tokens):
                raise SyntaxError("Unexpected EOF")

            next_token = self.tokens[self.pos + 1]

            if next_token.type == TokenType.ASSIGN:
                return self.parse_assignment()

            if next_token.type == TokenType.LBRACKET:
                node = self.parse_function_call()
                self.consume(TokenType.SEMICOLON)
                return node
        if t == TokenType.OUT:
            self.consume(TokenType.OUT)
            node = self.parse_expression()
            self.consume(TokenType.SEMICOLON)
            return OutNode(node)

        if t == TokenType.READ:
            if self.pos + 1 >= len(self.tokens):
                raise SyntaxError("Unexpected EOF")

            self.consume(TokenType.READ)
            self.consume(TokenType.LBRACKET)
            node = ReadNode(self.parse_expression())
            self.consume(TokenType.RBRACKET)

            self.consume(TokenType.ASSIGN)

            value = self.parse_expression()

            self.consume(TokenType.SEMICOLON)

            return AssignNode(node, value)
        if t == TokenType.EI:
            self.consume(TokenType.EI)
            self.consume(TokenType.SEMICOLON)
            return EINode()

        if t == TokenType.DI:
            self.consume(TokenType.DI)
            self.consume(TokenType.SEMICOLON)
            return DINode()

        print(self.current())

        raise SyntaxError("Invalid statement")

    def parse_assignment(self):
        name = self.consume(
            TokenType.IDENTIFIER
        ).value

        self.consume(TokenType.ASSIGN)
        value = self.parse_expression()
        self.consume(TokenType.SEMICOLON)

        return AssignNode(name, value)

    def parse_if(self):
        self.consume(TokenType.IF)
        self.consume(TokenType.LBRACKET)
        condition = self.parse_condition()
        self.consume(TokenType.RBRACKET)
        then_body = self.parse_block()
        else_body = None

        if self.current().type == TokenType.ELSE:
            self.advance()
            else_body = self.parse_block()

        return IfNode(
            condition,
            then_body,
            else_body
        )

    def parse_while(self):
        self.consume(TokenType.WHILE)
        self.consume(TokenType.LBRACKET)
        condition = self.parse_condition()
        self.consume(TokenType.RBRACKET)

        body = self.parse_block()

        return WhileNode(condition, body)

    def parse_return(self):
        self.consume(TokenType.RETURN)
        value = None

        if self.current().type != TokenType.SEMICOLON:
            value = self.parse_expression()

        self.consume(TokenType.SEMICOLON)

        return ReturnNode(value)

    def parse_function_call(self):
        name = self.consume(
            TokenType.IDENTIFIER
        ).value
        self.consume(TokenType.LBRACKET)
        args = []

        if self.current().type != TokenType.RBRACKET:
            args.append(
                self.parse_expression()
            )
            while self.current().type == TokenType.COMMA:
                self.advance()

                args.append(
                    self.parse_expression()
                )

        self.consume(TokenType.RBRACKET)

        return FunctionCallNode(name, args)

    def parse_condition(self):

        left = self.parse_expression()

        op = self.current().value

        if self.current().type not in (
                TokenType.EQ,
                TokenType.NE,
                TokenType.LT,
                TokenType.LE,
                TokenType.GR,
                TokenType.GE
        ):
            raise SyntaxError("Expected comparison")

        self.advance()

        right = self.parse_expression()

        return ConditionNode(left, op, right)

    def parse_expression(self):
        node = self.parse_term()

        while self.current().type in (
            TokenType.PLUS,
            TokenType.MINUS
        ):
            op = self.current().value
            self.advance()

            right = self.parse_term()

            node = BinaryOpNode(
                left=node,
                op=op,
                right=right
            )

        return node

    def parse_term(self):
        node = self.parse_factor()

        while self.current().type == TokenType.MUL:
            op = self.current().value
            self.advance()

            right = self.parse_factor()

            node = BinaryOpNode(
                node,
                op,
                right
            )

        return node

    def parse_factor(self):

        token = self.current()

        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)

        if token.type == TokenType.STRING:
            self.advance()
            return StringNode(token.value)

        if token.type == TokenType.CHAR:
            self.advance()
            return CharNode(token.value)

        if token.type == TokenType.MINUS:
            self.advance()

            return BinaryOpNode(
                NumberNode(0),
                "-",
                self.parse_factor()
            )

        if token.type == TokenType.IDENTIFIER:

            if (
                    self.pos + 1 < len(self.tokens)
                    and
                    self.tokens[self.pos + 1].type
                    == TokenType.LBRACKET
            ):
                return self.parse_function_call()

            self.advance()
            return IdentifierNode(token.value)

        if token.type == TokenType.LBRACKET:
            self.advance()

            expr = self.parse_expression()

            self.consume(TokenType.RBRACKET)

            return expr
        if token.type == TokenType.IN:
            self.consume(TokenType.IN)
            return InNode()

        if token.type == TokenType.READ:
            self.consume(TokenType.READ)
            self.consume(TokenType.LBRACKET)
            node = self.parse_expression()
            self.consume(TokenType.RBRACKET)
            return ReadNode(node)

        raise SyntaxError(
            f"Unexpected token {token.type}"
        )


