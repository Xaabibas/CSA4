from collections.abc import Callable

from AST import *


class Analyzer:
    variables: dict[str, int]
    functions: dict[str, int]
    visits: dict[type, Callable]

    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.visits = {
            VarDeclNode: self.visit_var_decl_node,
            IdentifierNode: self.visit_identifier_node,
            AssignNode: self.visit_assign_node,
            ConditionNode: self.visit_condition_node,
            IfNode: self.visit_if_node,
            WhileNode: self.visit_while_node,
            ReturnNode: self.visit_return_node,
            FunctionNode: self.visit_function_node,
            BinaryOpNode: self.visit_bin_op_node,
            InterruptFunctionNode: self.visit_interrupt_function_node,
            FunctionCallNode: self.visit_function_call_node,
            NumberNode: self.visit_number_node,
        }

    def analyze(self, program: ProgramNode):
        self.visit_program_node(program)

    def visit(self, node):
        if type(node) not in self.visits:
            return
        self.visits[type(node)](node)

    def visit_program_node(self, program: ProgramNode):
        for node in program.declarations:
            self.visit(node)

    def visit_var_decl_node(self, node):
        if node.name in self.variables:
            raise Exception(f"Variable '{node.name}' already declared")

        self.variables[node.name] = True

        if node.value:
            self.visit(node.value)

    def visit_identifier_node(self, node):
        if node.name not in self.variables:
            raise Exception(f"Undefined variable '{node.name}'")

    def visit_assign_node(self, node):
        if isinstance(node.name, ReadNode):
            self.visit(node.name)
        elif node.name not in self.variables:
            raise Exception(f"Undefined variable '{node.name}'")

        self.visit(node.value)

    def visit_bin_op_node(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_condition_node(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_if_node(self, node):
        self.visit_condition_node(node.condition)

        old_vars = self.variables.copy()

        for stmt in node.then_block:
            self.visit(stmt)

        self.variables = old_vars

        if node.else_block:
            for stmt in node.else_block:
                self.visit(stmt)

        self.variables = old_vars

    def visit_while_node(self, node):
        self.visit_condition_node(node.condition)
        old_vars = self.variables.copy()

        for stmt in node.body:
            self.visit(stmt)

        self.variables = old_vars

    def visit_return_node(self, node):
        if node.value:
            self.visit(node.value)

    def visit_function_node(self, node):
        if node.name in self.functions:
            raise Exception(f"Function '{node.name}' already declared")

        self.functions[node.name] = len(node.params)

        for param in node.params:
            self.variables[param] = True

        for stmt in node.body:
            self.visit(stmt)

    def visit_interrupt_function_node(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_function_call_node(self, node):
        if node.name not in self.functions:
            raise Exception(f"Undefined function '{node.name}'")

        expected = self.functions[node.name]
        actual = len(node.args)

        if expected != actual:
            raise Exception(f"Function '{node.name}' expects {expected} arguments, got {actual}")

        for arg in node.args:
            self.visit(arg)
    def visit_number_node(self, node):
        if -2**19 <= node.value <= 2**19 - 1:
            return
        raise Exception(f"Number {node.value} too large")