from AST import *


class Analyzer:
    variables: {}
    functions: {}
    visits: {}

    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.visits = {
            VarDeclNode: self.visitVarDeclNode,
            IdentifierNode: self.visitIdentifierNode,
            AssignNode: self.visitAssignNode,
            ConditionNode: self.visitConditionNode,
            IfNode: self.visitIfNode,
            WhileNode: self.visitWhileNode,
            ReturnNode: self.visitReturnNode,
            FunctionNode: self.visitFunctionNode,
            BinaryOpNode: self.visitBinOpNode,
            InterruptFunctionNode: self.visitInterruptFunctionNode,
            FunctionCallNode: self.visitFunctionCallNode
        }

    def analyze(self, program: ProgramNode):
        self.visitProgramNode(program)

    def visit(self, node):
        if type(node) not in self.visits:
            return
        self.visits[type(node)](node)


    def visitProgramNode(self, program: ProgramNode):
        for node in program.declarations:
            self.visit(node)

    def visitVarDeclNode(self, node):
        if node.name in self.variables:
            raise Exception(
                f"Variable '{node.name}' already declared"
            )

        self.variables[node.name] = True

        if node.value:
            self.visit(node.value)


    def visitIdentifierNode(self, node):
        if node.name not in self.variables:
            raise Exception(
                f"Undefined variable '{node.name}'"
            )

    def visitAssignNode(self, node):
        if isinstance(node.name, ReadNode):
            self.visit(node.name)
        elif node.name not in self.variables:
            raise Exception(
                f"Undefined variable '{node.name}'"
            )

        self.visit(node.value)

    def visitBinOpNode(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visitConditionNode(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visitIfNode(self, node):
        self.visitConditionNode(node.condition)

        old_vars = self.variables.copy()

        for stmt in node.then_block:
            self.visit(stmt)

        self.variables = old_vars

        if node.else_block:
            for stmt in node.else_block:
                self.visit(stmt)

        self.variables = old_vars

    def visitWhileNode(self, node):
        self.visitConditionNode(node.condition)
        old_vars = self.variables.copy()

        for stmt in node.body:
            self.visit(stmt)

        self.variables = old_vars

    def visitReturnNode(self, node):
        if node.value:
            self.visit(node.value)

    def visitFunctionNode(self, node):
        if node.name in self.functions:
            raise Exception(
                f"Function '{node.name}' already declared"
            )

        self.functions[node.name] = len(node.params)

        for param in node.params:
            self.variables[param] = True

        for stmt in node.body:
            self.visit(stmt)

    def visitInterruptFunctionNode(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visitFunctionCallNode(self, node):
        if node.name not in self.functions:
            raise Exception(
                f"Undefined function '{node.name}'"
            )

        expected = self.functions[node.name]
        actual = len(node.args)

        if expected != actual:
            raise Exception(
                f"Function '{node.name}' expects "
                f"{expected} arguments, got {actual}"
            )

        for arg in node.args:
            self.visit(arg)