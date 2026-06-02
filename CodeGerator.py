from AST import *
from CommandTypes import AddrMode, Command, OpCode


class CodeGenerator:
    def __init__(self, start=2048):
        self.code = []

        self.variables = {}
        self.functions = {}
        self.locals = {}
        self.memory = {}

        self.local_count = 0

        self.data_addr = 128
        self.tmp_addr = 256
        self.string_addr = 65536
        self.start = start

        self.visits = {
            ProgramNode: self.visit_program_node,
            VarDeclNode: self.visit_var_decl_node,
            AssignNode: self.visit_assign_node,
            ConditionNode: self.visit_condition_node,
            IfNode: self.visit_if_node,
            WhileNode: self.visit_while_node,
            FunctionNode: self.visit_function_node,
            FunctionCallNode: self.visit_function_call_node,
            ReturnNode: self.visit_return_node,
            InterruptFunctionNode: self.visit_interrupt_function_node,
            InNode: self.visit_in_node,
            OutNode: self.visit_out_node,
            ReadNode: self.visit_read_node,
            DINode: self.visit_di_node,
            EINode: self.visit_ei_node,
        }

    def generate(self, program):
        self.visit_program_node(program)

    def collect_symbols(self, program):
        for decl in program.declarations:
            if isinstance(decl, VarDeclNode):
                self.variables[decl.name] = self.data_addr
                self.data_addr += 1

            elif isinstance(decl, FunctionNode):
                self.functions[decl.name] = None
            elif isinstance(decl, InterruptFunctionNode):
                self.memory[decl.port] = None

    def emit(self, op_code, addr_mode, arg):
        self.code.append(Command(op_code, addr_mode, arg))

    def visit(self, node):
        self.visits[type(node)](node)

    def visit_program_node(self, program):
        self.collect_symbols(program)

        self.emit(OpCode.DI, AddrMode.DIRECT, 0)
        start_jmp = len(self.code)

        self.emit(OpCode.JMP, AddrMode.DIRECT_LOAD, 0)

        for decl in program.declarations:
            if isinstance(decl, (FunctionNode, InterruptFunctionNode)):
                self.visit(decl)

        main_addr = len(self.code)

        self.code[start_jmp].arg = main_addr + self.start

        for decl in program.declarations:
            if not isinstance(decl, (FunctionNode, InterruptFunctionNode)):
                self.visit(decl)

        self.emit(OpCode.HALT, AddrMode.DIRECT, 0)

    def visit_var_decl_node(self, node):
        if node.name not in self.variables and node.name not in self.locals:
            self.locals[node.name] = self.local_count + 1
        if node.value is None and node.name not in self.locals:
            self.local_count += 1
            return

        self.generate_expression(node.value)
        self.local_count += 1
        if node.name not in self.variables:
            self.emit(OpCode.PUSH, AddrMode.DIRECT, 0)
            return

        self.emit(OpCode.STR, AddrMode.DIRECT, self.variables[node.name])

    def generate_expression(self, node):
        if isinstance(node, NumberNode):
            self.emit(OpCode.LOAD, AddrMode.DIRECT_LOAD, node.value)
        elif isinstance(node, IdentifierNode):
            if node.name in self.locals:
                self.emit(OpCode.LOAD, AddrMode.RELATIVE_SP, -self.locals[node.name] + self.local_count)
                return
            self.emit(OpCode.LOAD, AddrMode.DIRECT, self.variables[node.name])
        elif isinstance(node, BinaryOpNode):
            self.generate_expression(node.right)
            tmp = self.tmp_addr
            self.tmp_addr += 1

            self.emit(OpCode.STR, AddrMode.DIRECT, tmp)

            self.generate_expression(node.left)

            if node.op == "+":
                op_code = OpCode.ADD
            elif node.op == "-":
                op_code = OpCode.SUB
            elif node.op == "+*":
                op_code = OpCode.ADC
            elif node.op == "/":
                op_code = OpCode.DIV
            elif node.op == "%":
                op_code = OpCode.MOD
            else:
                op_code = OpCode.MUL

            self.emit(op_code, AddrMode.DIRECT, tmp)

            self.tmp_addr -= 1
        elif isinstance(node, CharNode):
            self.emit(OpCode.LOAD, AddrMode.DIRECT_LOAD, ord(node.value))
        elif isinstance(node, StringNode):
            length = len(node.value)

            self.memory[self.string_addr] = length
            self.string_addr += 1

            for c in node.value:
                self.memory[self.string_addr] = ord(c)
                self.string_addr += 1

            self.emit(OpCode.LOAD, AddrMode.DIRECT_LOAD, self.string_addr - length - 1)

        else:
            self.visit(node)

    def visit_assign_node(self, node):
        if isinstance(node.name, ReadNode):
            self.generate_expression(node.name.value)
            self.emit(OpCode.STR, AddrMode.DIRECT, self.tmp_addr)
            self.tmp_addr += 1
            self.generate_expression(node.value)
            self.tmp_addr -= 1
            self.emit(OpCode.STR, AddrMode.RELATIVE_INDIRECT, self.tmp_addr)

            return
        self.generate_expression(node.value)
        if node.name in self.locals:
            self.emit(OpCode.STR, AddrMode.RELATIVE_SP, -self.locals[node.name] + self.local_count)
            return
        self.emit(OpCode.STR, AddrMode.DIRECT, self.variables[node.name])

    def visit_condition_node(self, condition):
        tmp = self.tmp_addr
        self.tmp_addr += 1

        if condition.op in ("==", "!=", "<=", ">"):
            self.generate_expression(condition.left)
            self.emit(OpCode.STR, AddrMode.DIRECT, tmp)
            self.generate_expression(condition.right)
        else:
            self.generate_expression(condition.right)
            self.emit(OpCode.STR, AddrMode.DIRECT, tmp)
            self.generate_expression(condition.left)

        self.emit(OpCode.COMP, AddrMode.DIRECT, tmp)

        self.tmp_addr -= 1

        if condition.op == "==":
            self.emit(OpCode.JNE, AddrMode.DIRECT_LOAD, 0)
        elif condition.op == "!=":
            self.emit(OpCode.JEQ, AddrMode.DIRECT_LOAD, 0)
        elif condition.op == "<=":
            self.emit(OpCode.JLT, AddrMode.DIRECT_LOAD, 0)
        elif condition.op == ">=":
            self.emit(OpCode.JLT, AddrMode.DIRECT_LOAD, 0)
        elif condition.op == "<":
            self.emit(OpCode.JGE, AddrMode.DIRECT_LOAD, 0)
        elif condition.op == ">":
            self.emit(OpCode.JGE, AddrMode.DIRECT_LOAD, 0)

    def visit_if_node(self, node):
        self.visit(node.condition)

        then_pos = len(self.code) - 1

        old_locals = self.locals.copy()
        old_count = self.local_count

        for stmt in node.then_block:
            self.visit(stmt)
        for _ in range(self.local_count - old_count):
            self.emit(OpCode.POP, AddrMode.DIRECT, 0)

        self.locals = old_locals
        self.local_count = old_count

        if node.else_block:
            else_pos = len(self.code)
            self.emit(OpCode.JMP, AddrMode.DIRECT_LOAD, 0)
            self.code[then_pos].arg = len(self.code) + self.start

            old_locals = self.locals.copy()
            old_count = self.local_count

            for stmt in node.else_block:
                self.visit(stmt)
            for _ in range(self.local_count - old_count):
                self.emit(OpCode.POP, AddrMode.DIRECT, 0)

            self.locals = old_locals
            self.local_count = old_count
            self.code[else_pos].arg = len(self.code) + self.start
            return

        self.code[then_pos].arg = len(self.code) + self.start

    def visit_while_node(self, node):
        loop_start = len(self.code) + self.start

        self.visit(node.condition)

        break_pos = len(self.code) - 1

        old_locals = self.locals.copy()
        old_count = self.local_count

        for stmt in node.body:
            self.visit(stmt)

        for _ in range(self.local_count - old_count):
            self.emit(OpCode.POP, AddrMode.DIRECT, 0)

        self.locals = old_locals
        self.local_count = old_count

        self.emit(OpCode.JMP, AddrMode.DIRECT_LOAD, loop_start)

        self.code[break_pos].arg = len(self.code) + self.start

    def visit_function_call_node(self, node):
        for arg in reversed(node.args):
            self.generate_expression(arg)
            self.emit(OpCode.PUSH, AddrMode.DIRECT, 0)

        call_pos = len(self.code)

        self.emit(OpCode.CALL, AddrMode.DIRECT_LOAD, self.functions[node.name])

        for _ in node.args:
            self.emit(OpCode.POP, AddrMode.DIRECT, 0)

        return call_pos

    def visit_return_node(self, node):
        if node.value:
            self.generate_expression(node.value)
        for i in range(self.local_count):
            self.emit(OpCode.POP, AddrMode.DIRECT, 0)

        self.emit(OpCode.RET, AddrMode.DIRECT, 0)

    def visit_interrupt_function_node(self, node):
        self.memory[node.port] = len(self.code) + self.start

        self.locals = {}
        self.local_count = 0

        for stmt in node.body:
            self.visit(stmt)

        for i in range(self.local_count):
            self.emit(OpCode.POP, AddrMode.DIRECT, 0)

        self.emit(OpCode.IRET, AddrMode.DIRECT, 0)

    def visit_function_node(self, node):
        self.functions[node.name] = len(self.code) + self.start

        self.locals = {}
        self.local_count = 0

        for i, param in enumerate(node.params):
            self.locals[param] = -i - 1

        for stmt in node.body:
            self.visit(stmt)

        if self.code[-1].op_code != OpCode.RET:
            for i in range(self.local_count):
                self.emit(OpCode.POP, AddrMode.DIRECT, 0)
            self.emit(OpCode.RET, AddrMode.DIRECT, 0)

    def visit_in_node(self, node):
        self.emit(OpCode.IN, AddrMode.DIRECT_LOAD, 0)

    def visit_out_node(self, node):
        self.generate_expression(node.value)
        self.emit(OpCode.OUT, AddrMode.DIRECT_LOAD, 1)

    def visit_read_node(self, node):
        self.generate_expression(node.value)

        self.emit(OpCode.STR, AddrMode.DIRECT, self.tmp_addr)

        self.emit(OpCode.LOAD, AddrMode.RELATIVE_INDIRECT, self.tmp_addr)

    def visit_ei_node(self, node):
        self.emit(OpCode.EI, AddrMode.DIRECT, 0)

    def visit_di_node(self, node):
        self.emit(OpCode.DI, AddrMode.DIRECT, 0)
