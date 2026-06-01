from AST import *
from CommandTypes import Command, OpCode, AddrMode


class CodeGenerator:

    def __init__(self, start=512):
        self.code = []

        self.variables = {}
        self.functions = {}
        self.global_ = {}
        self.locals = {}

        self.local_count = 0

        self.data_addr = 128
        self.tmp_addr = 256
        self.start = start

        self.visits = {
            ProgramNode: self.visitProgramNode,
            VarDeclNode: self.visitVarDeclNode,
            AssignNode: self.visitAssignNode,
            ConditionNode: self.visitConditionNode,
            IfNode: self.visitIfNode,
            WhileNode: self.visitWhileNode,
            FunctionNode: self.visitFunctionNode,
            FunctionCallNode: self.visitFunctionCallNode,
            ReturnNode: self.visitReturnNode,
            InterruptFunctionNode: self.visitInterruptFunctionNode
        }

    def generate(self, program):
        self.visitProgramNode(program)

    def collect_symbols(self, program):
        for decl in program.declarations:
            if isinstance(decl, VarDeclNode):
                self.variables[decl.name] = self.data_addr
                self.data_addr += 1

            elif isinstance(decl, FunctionNode):
                self.functions[decl.name] = None
            elif isinstance(decl, InterruptFunctionNode):
                self.global_[decl.port] = None

    def emit(self, op_code, addr_mode, arg):
        self.code.append(Command(op_code, addr_mode, arg))

    def visit(self, node):
        self.visits[type(node)](node)

    def visitProgramNode(self, program):
        self.collect_symbols(program)

        start_jmp = len(self.code)

        self.emit(
            OpCode.JMP,
            AddrMode.DIRECT_LOAD,
            0
        )

        for decl in program.declarations:
            if isinstance(decl, (FunctionNode, InterruptFunctionNode)):
                self.visit(decl)

        main_addr = len(self.code)

        self.code[start_jmp].arg = main_addr + self.start

        for decl in program.declarations:
            if not isinstance(decl, (FunctionNode, InterruptFunctionNode)):
                self.visit(decl)

        self.emit(
            OpCode.HALT,
            AddrMode.DIRECT,
            0
        )

    def visitVarDeclNode(self, node):
        if node.name not in self.variables:
            self.locals[node.name] = self.local_count + 1
        if node.value is None:
            self.local_count += 1
            return

        self.generate_expression(node.value)
        self.local_count += 1
        if node.name not in self.variables:
            self.emit(
                OpCode.PUSH,
                AddrMode.DIRECT,
                0
            )
            return

        self.emit(
            OpCode.STR,
            AddrMode.DIRECT,
            self.variables[node.name]
        )

    def generate_expression(self, node):
        if isinstance(node, NumberNode):
            self.emit(
                OpCode.LOAD,
                AddrMode.DIRECT_LOAD,
                node.value
            )
        elif isinstance(node, IdentifierNode):
            if node.name in self.locals:
                self.emit(
                    OpCode.LOAD,
                    AddrMode.RELATIVE_SP,
                    -self.locals[node.name] + self.local_count
                )
                return
            self.emit(
                OpCode.LOAD,
                AddrMode.DIRECT,
                self.variables[node.name]
            )
        elif isinstance(node, BinaryOpNode):
            self.generate_expression(node.right)
            tmp = self.tmp_addr
            self.tmp_addr += 1

            self.emit(
                OpCode.STR,
                AddrMode.DIRECT,
                tmp
            )

            self.generate_expression(node.left)

            if node.op == "+":
                op_code = OpCode.ADD
            elif node.op == "-":
                op_code = OpCode.SUB
            else:
                op_code = OpCode.MUL

            self.emit(
                op_code,
                AddrMode.DIRECT,
                tmp
            )

            self.tmp_addr -= 1
        else:
            self.visit(node)

    def visitAssignNode(self, node):
        self.generate_expression(node.value)

        if node.name in self.locals:
            self.emit(
                OpCode.STR,
                AddrMode.RELATIVE_SP,
                -self.locals[node.name]
            )
            return
        self.emit(
            OpCode.STR,
            AddrMode.DIRECT,
            self.variables[node.name]
        )

    def visitConditionNode(self, condition):
        tmp = self.tmp_addr
        self.tmp_addr += 1

        if condition.op in ("==", "!=", "<=", ">"):
            self.generate_expression(condition.left)
            self.emit(
                OpCode.STR,
                AddrMode.DIRECT,
                tmp
            )
            self.generate_expression(condition.right)
        else:
            self.generate_expression(condition.right)
            self.emit(
                OpCode.STR,
                AddrMode.DIRECT,
                tmp
            )
            self.generate_expression(condition.left)

        self.emit(
            OpCode.COMP,
            AddrMode.DIRECT,
            tmp
        )

        self.tmp_addr -= 1

        if condition.op == "==":
            self.emit(
                OpCode.JNE,
                AddrMode.DIRECT_LOAD,
                0
            )
        elif condition.op == "!=":
            self.emit(
                OpCode.JEQ,
                AddrMode.DIRECT_LOAD,
                0
            )
        elif condition.op == "<=":
            self.emit(
                OpCode.JLT,
                AddrMode.DIRECT_LOAD,
                0
            )
        elif condition.op == ">=":
            self.emit(
                OpCode.JLT,
                AddrMode.DIRECT_LOAD,
                0
            )
        elif condition.op == "<":
            self.emit(
                OpCode.JGE,
                AddrMode.DIRECT_LOAD,
                0
            )
        elif condition.op == ">":
            self.emit(
                OpCode.JGE,
                AddrMode.DIRECT_LOAD,
                0
            )

    def visitIfNode(self, node):
        self.visit(node.condition)

        then_pos = len(self.code) - 1

        for stmt in node.then_block:
            self.visit(stmt)

        if node.else_block:
            else_pos = len(self.code)
            self.emit(
                OpCode.JMP,
                AddrMode.DIRECT_LOAD,
                0
            )
            self.code[then_pos].arg = len(self.code) + self.start

            for stmt in node.else_block:
                self.visit(stmt)
            self.code[else_pos].arg = len(self.code) + self.start
            return

        self.code[then_pos].arg = len(self.code) + self.start

    def visitWhileNode(self, node):
        loop_start = len(self.code)

        self.visit(node.condition)

        break_pos = len(self.code) - 1

        for stmt in node.body:
            self.visit(stmt)

        self.emit(
            OpCode.JMP,
            AddrMode.DIRECT_LOAD,
            loop_start
        )

        self.code[break_pos].arg = len(self.code) + self.start

    def visitFunctionCallNode(self, node):
        for arg in reversed(node.args):
            self.generate_expression(arg)
            self.emit(
                OpCode.PUSH,
                AddrMode.DIRECT,
                0)

        call_pos = len(self.code)

        self.emit(
            OpCode.CALL,
            AddrMode.DIRECT_LOAD,
            self.functions[node.name]
        )

        for _ in node.args:
            self.emit(
                OpCode.INC_SP,
                AddrMode.DIRECT,
                0
            )

        return call_pos

    def visitReturnNode(self, node):
        if node.value:
            self.generate_expression(node.value)

        for i in range(self.local_count):
            self.emit(
                OpCode.INC_SP,
                AddrMode.DIRECT,
                0
            )

        self.emit(
            OpCode.RET,
            AddrMode.DIRECT,
            0
        )

    def visitInterruptFunctionNode(self, node):
        self.global_[node.port] = len(self.code)

        for stmt in node.body:
            self.visit(stmt)

        self.emit(
            OpCode.IRET,
            AddrMode.DIRECT,
            0
        )

    def visitFunctionNode(self, node):
        self.functions[node.name] = len(self.code) + self.start

        old_variables = self.variables
        self.variables = {}

        self.locals = {}
        self.local_count = 0

        for i, param in enumerate(node.params):
            self.locals[param] = -i - 1

        for stmt in node.body:
            self.visit(stmt)

        if self.code[-1].op_code != OpCode.RET:
            self.emit(
                OpCode.RET,
                AddrMode.DIRECT,
                0
            )

        self.variables = old_variables
