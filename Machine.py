import logging
import sys
from collections.abc import Callable

from ALU import ALU
from CommandTypes import AddrMode, Command, OpCode, decode, read_commands_from_file
from External import IOController
from MagicNumber import MagicNumber
from Memory import Memory


class Machine:
    io_controller: IOController = IOController()
    AC: int = 0
    BR: int | Command = 0
    PS: int = 0
    DR: int | Command = 0
    SP: int | Command = 0
    CR: int | Command = 0
    IP: int | Command = 0
    AR: int = 0
    ZEROES: int = 0
    memory_bus: int | Command = 0
    DR_selector: bool = True  # True - alu; False - memory

    def __init__(self, memory):
        self.alu = ALU()
        self.memory = memory

    def load_ac(self):
        self.alu.left = self.AC

    def load_br(self):
        self.alu.left = self.BR

    def load_ps(self):
        self.alu.left = self.PS

    def load_dr(self):
        self.alu.right = self.DR

    def load_sp(self):
        self.alu.right = self.SP

    def load_cr(self):
        self.alu.right = self.CR

    def load_ip(self):
        self.alu.right = self.IP

    def load_left_zero(self):
        self.alu.left = 0

    def load_right_zero(self):
        self.alu.right = 0

    def latch_ac(self):
        self.AC = self.alu.out

    def latch_br(self):
        self.BR = self.alu.out

    def latch_ps(self):
        self.PS = self.alu.out & (2**MagicNumber.PS_LEN.value - 1)

    def latch_ps_flags(self):
        nzvc = (self.alu.N << 3) | (self.alu.Z << 2) | (self.alu.V << 1) | self.alu.C
        self.PS = (self.PS & 0x30) | nzvc

    def ei(self):
        self.PS = self.PS | 0x10

    def di(self):
        self.PS = self.PS & 0x2F

    def latch_ar(self):
        self.AR = self.alu.out & (2**MagicNumber.ADDR_LEN.value - 1)

    def latch_ip(self):
        self.IP = self.alu.out

    def latch_cr(self):
        self.CR = self.memory_bus

    def latch_sp(self):
        self.SP = self.alu.out & (2**MagicNumber.ADDR_LEN.value - 1)

    def latch_dr(self):
        if self.DR_selector:
            self.DR = self.alu.out
        else:
            self.DR = self.memory_bus
        self.DR_selector = True

    def write(self, tick_callback, now: Callable):
        self.memory.write(self.AR, self.DR, tick_callback, now)

    def read(self, tick_callback, now: Callable):
        self.memory_bus = self.memory.read(self.AR, tick_callback, now)

    def in_(self):
        self.AC = self.io_controller.buffer

    def out(self):
        self.io_controller.buffer = self.AC

    def latch_iport(self):
        self.BR = self.io_controller.IPort


class ControlUnit:
    def __init__(self, file):
        self.tick = 0
        self.memory = Memory()
        self.machine = Machine(self.memory)
        self.address_fetch = {
            AddrMode.DIRECT: self.direct_addr,
            AddrMode.RELATIVE_IP: self.relative_ip_addr,
            AddrMode.RELATIVE_SP: self.relative_sp_addr,
            AddrMode.RELATIVE_INDIRECT: self.relative_indirect,
            AddrMode.DIRECT_LOAD: self.direct_load,
        }
        self.execution = {
            OpCode.NOP: self.nope,
            OpCode.HALT: self.halt,
            OpCode.IN: self.in_,
            OpCode.OUT: self.out,
            OpCode.PUSH: self.push,
            OpCode.POP: self.pop,
            OpCode.EI: self.enable_interrupt,
            OpCode.DI: self.disable_interrupt,
            OpCode.LOAD: self.load,
            OpCode.STR: self.store,
            OpCode.CALL: self.call,
            OpCode.RET: self.return_,
            OpCode.IRET: self.interrupt_return,
            OpCode.ADD: self.add,
            OpCode.SUB: self.sub,
            OpCode.MUL: self.mul,
            OpCode.ADC: self.adc,
            OpCode.DIV: self.div,
            OpCode.MOD: self.mod,
            OpCode.AND: self.and_,
            OpCode.OR: self.or_,
            OpCode.NEG: self.neg,
            OpCode.CLR: self.clear,
            OpCode.COMP: self.compare,
            OpCode.JMP: self.jump,
            OpCode.JEQ: self.jump_if_equal,
            OpCode.JNE: self.jump_if_not_equal,
            OpCode.JMI: self.jump_if_minus,
            OpCode.JPL: self.jump_if_plus,
            OpCode.JGE: self.jump_if_greater_or_equal,
            OpCode.JLT: self.jump_if_less,
        }
        self.file = file
        self.instructions = []

    def snapshot(self, info):
        return (
            f"Tick #{self.tick:^5} - "
            + f"AC: {self.machine.AC:010}, BR: {self.machine.BR:010}, PS: {self.machine.PS:03}, DR: {self.machine.DR:010}, CR: {self.machine.CR:010}, IP: {self.machine.IP:07}, SP: {self.machine.SP:07}, AR: {self.machine.IP:07}"
            + f"{'' if info == '' else '; ' + info}"
        )

    def tick_(self, info=""):
        self.tick += 1
        log = self.snapshot(info)
        logging.debug(log)
        self.file.write(log + "\n")

        self.machine.io_controller.update(self.tick)

    def command_repr(self):
        if isinstance(self.machine.CR, Command):
            return f"{self.machine.AR} - {self.machine.CR.to_hex_code()} - {self.machine.CR.to_string()}"

        return "0"

    def now(self):
        return self.tick

    def instruction_fetch_stage(self):
        self.machine.load_ip()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_br()
        self.machine.latch_ar()
        self.tick_(info="INSTRUCTION FETCH")

        self.machine.read(self.tick_, self.now)

        self.machine.latch_cr()
        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.inc()
        self.machine.latch_ip()

        if isinstance(self.machine.CR, int):
            self.machine.CR = decode(self.machine.CR)

        self.tick_(
            info="INSTRUCTION FETCH; "
            + f"{self.machine.AR} - {self.machine.CR.to_hex_code()} - {self.machine.CR.to_string()}; "
        )

        self.instructions.append(f"{self.machine.AR} - {self.machine.CR.to_hex_code()} - {self.machine.CR.to_string()}")

    def operand_fetch_stage(self):

        op_code = self.machine.CR.op_code
        if not (op_code.value & 0xF0):
            return

        addr_mode = self.machine.CR.addr_mode
        self.address_fetch[addr_mode]()

    def direct_addr(self):
        self.machine.load_cr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

    def relative_ip_addr(self):
        self.machine.load_br()
        self.machine.load_cr()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

    def relative_sp_addr(self):
        self.machine.load_cr()
        self.machine.alu.extend()
        self.machine.latch_br()
        self.tick_()

        self.machine.load_br()
        self.machine.load_sp()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

    def relative_indirect(self):
        self.machine.load_cr()
        self.machine.alu.extend()
        self.machine.latch_ar()
        self.tick_()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

    def direct_load(self):
        self.machine.load_cr()
        self.machine.alu.extend()
        self.machine.latch_dr()
        self.tick_()

    def execute_stage(self):
        op_code = self.machine.CR.op_code
        self.execution[op_code]()

    def nope(self):
        pass

    def halt(self):
        raise SystemExit

    def in_(self):
        register_selector = self.machine.CR.addr_mode.value
        port = self.machine.CR.arg

        self.machine.io_controller.in_(port, register_selector)
        self.tick_(info=f"IN {port}")

        self.machine.in_()
        self.tick_(info=f"IN {port}")

    def out(self):
        port = self.machine.CR.arg
        self.machine.out()
        self.tick_(info=f"OUT {port}")

        self.machine.io_controller.out(port)
        self.tick_(info=f"OUT {port}")

    def push(self):
        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.invert_left()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.machine.latch_sp()
        self.tick_()

        self.machine.load_ac()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_dr()
        self.tick_()

        self.machine.write(self.tick_, self.now)

    def pop(self):
        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.inc()
        self.machine.latch_sp()
        self.tick_()

    def enable_interrupt(self):
        self.machine.ei()
        self.tick_()

    def disable_interrupt(self):
        self.machine.di()
        self.tick_()

    def load(self):
        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ac()
        self.tick_()

    def store(self):
        self.machine.load_ac()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_dr()
        self.tick_()

        self.machine.write(self.tick_, self.now)

    def call(self):
        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_br()
        self.tick_()

        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.invert_left()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.machine.latch_sp()
        self.tick_()

        self.machine.load_ip()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_dr()
        self.tick_()

        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_ip()

        self.machine.write(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

    def return_(self):
        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_()

        self.machine.load_sp()
        self.machine.alu.inc()
        self.machine.latch_sp()
        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

        self.machine.load_dr()
        self.machine.alu.sum()
        self.machine.latch_ip()
        self.tick_()

    def interrupt_return(self):
        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.machine.latch_br()
        self.tick_()

        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.inc()
        self.machine.latch_sp()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()

        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ip()
        self.tick_()

        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.machine.latch_br()
        self.tick_()

        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.inc()
        self.machine.latch_sp()

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()
        self.tick_()

        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ps()
        self.tick_()

    def add(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.sum()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def sub(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.invert_right()
        self.machine.alu.inc()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def mul(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.mul()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def div(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.div()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def mod(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.mod()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def adc(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.adc(self.machine.PS & 0x1)
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def and_(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.and_()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def or_(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.invert_left()
        self.machine.alu.invert_right()
        self.machine.alu.and_()
        self.machine.latch_br()
        self.tick_()

        self.machine.load_br()
        self.machine.alu.invert_left()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def neg(self):
        self.machine.load_ac()
        self.machine.load_right_zero()
        self.machine.alu.invert_left()
        self.machine.alu.inc()
        self.machine.latch_ac()
        self.machine.latch_ps_flags()
        self.tick_()

    def clear(self):
        self.machine.load_left_zero()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_ac()
        self.tick_()

    def compare(self):
        self.machine.load_ac()
        self.machine.load_dr()
        self.machine.alu.invert_right()
        self.machine.alu.inc()
        self.machine.latch_ps_flags()
        self.tick_()

    def jump(self):
        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ip()
        self.tick_()

    def jump_if_equal(self):
        if self.machine.PS & 0x04:
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def jump_if_not_equal(self):
        if not self.machine.PS & 0x04:
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def jump_if_plus(self):
        if not self.machine.PS & 0x08:
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def jump_if_minus(self):
        if self.machine.PS & 0x08:
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def jump_if_greater_or_equal(self):
        if (self.machine.PS & 0x02) == ((self.machine.PS & 0x08) >> 2):
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def jump_if_less(self):
        if (self.machine.PS & 0x02) != ((self.machine.PS & 0x08) >> 2):
            self.machine.load_dr()
            self.machine.load_left_zero()
            self.machine.alu.sum()
            self.machine.latch_ip()
        self.tick_()

    def interrupt_stage(self):
        self.machine.io_controller.check_interrupts()

        if (not (self.machine.PS & 0x10)) or (self.machine.PS & 0x20):
            return

        if not self.machine.io_controller.IREQ:
            return
        self.handle_interrupt()

    def handle_interrupt(self):
        self.machine.load_ps()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_dr()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.invert_left()
        self.machine.alu.sum()
        self.machine.latch_sp()
        self.machine.latch_ar()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.write(self.tick_, self.now)
        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.invert_left()
        self.machine.alu.sum()
        self.machine.latch_sp()
        self.machine.latch_ar()

        self.machine.load_ip()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_dr()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.write(self.tick_, self.now)

        self.machine.PS |= 0x20

        self.machine.latch_iport()
        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ip()
        self.tick_(info="HANDLE INTERRUPT")

        self.machine.io_controller.IREQ = False

    def cycle(self):
        self.instruction_fetch_stage()
        self.operand_fetch_stage()
        self.execute_stage()
        self.interrupt_stage()

    def load_code(self, code, start=2048):
        for addr, command in enumerate(code):
            self.memory.memory[addr + start] = command
        self.machine.IP = start

    def load_memory(self, memory):
        for addr, data in memory.items():
            self.memory.memory[addr] = data

    def load_input(self, input_tokens):
        self.machine.io_controller = IOController(input_tokens)

    def run(self, limit: int = 200000):
        cnt = 0
        try:
            for i in range(limit):
                cnt = i
                self.cycle()
            else:
                raise Exception("Op limit")
        except SystemExit:
            print("Executed instructions:", cnt)
            print("Output buffer (str):", self.machine.io_controller.devices[1].buffer_str)
            print("Output buffer (int):", self.machine.io_controller.devices[1].buffer_int)


if __name__ == "__main__":
    assert 4 <= len(sys.argv) <= 5, (
        "Wrong argument count: python Machine.py <source_file> <memory_file> <debug_file> [<input_file>] "
    )

    if len(sys.argv) == 4:
        _, source_file, memory_file, debug_file = sys.argv
        input_file = None
    else:
        _, source_file, memory_file, debug_file, input_file = sys.argv

    code = read_commands_from_file(source_file)

    with open(debug_file, "w", encoding="utf-8") as debug:
        cu = ControlUnit(debug)

        cu.load_code(code)

        with open(memory_file, encoding="utf-8") as file:
            memory_text = file.read()
            memory = eval(memory_text)

            cu.load_memory(memory)

        if input_file is not None:
            with open(input_file, encoding="utf-8") as file:
                input_text = file.read()
                input_tokens = eval(input_text)

                cu.load_input(input_tokens)

        cu.run()
