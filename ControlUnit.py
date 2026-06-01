from io import TextIOWrapper

from CommandTypes import AddrMode, OpCode, Command
from Machine import Machine
from Memory import Memory
import logging


class ControlUnit:
    machine: Machine
    memory: Memory = Memory()
    tick: int = 0
    file: TextIOWrapper
    instructions: []

    def __init__(self, file):
        self.machine = Machine(self.memory)
        self.address_fetch = {
            AddrMode.DIRECT: self.direct_addr,
            AddrMode.RELATIVE_IP: self.relative_ip_addr,
            AddrMode.RELATIVE_SP: self.relative_sp_addr,
            AddrMode.RELATIVE_INDIRECT: self.relative_indirect,
            AddrMode.DIRECT_LOAD: self.direct_load
        }
        self.execution = {
            OpCode.NOP: self.nope,
            OpCode.HALT: self.halt,
            OpCode.IN: self.in_,
            OpCode.OUT: self.out,
            OpCode.PUSH: self.push,
            OpCode.POP: self.pop,
            OpCode.INC_SP: self.inc_sp,
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
            OpCode.JLT: self.jump_if_less
        }
        self.file = file
        self.instructions = []

    def tick_(self, info=""):
        self.tick += 1
        log = (f"Tick #{self.tick}; {info}"
               f"AC: {self.machine.AC}, BR: {self.machine.BR}, PS:{self.machine.PS}, DR: {self.machine.DR}, CR:{self.machine.CR}, IP: {self.machine.IP}, SP: {self.machine.SP}; AR: {self.machine.AR}" +
               # self.command_repr())
               "")
        logging.debug(log)
        print(log)
        self.file.write(log + "\n")
        if self.machine.PS & 0x20 or self.machine.io_controller.IREQ:
            return
        self.machine.io_controller.update(self.tick)

    def command_repr(self):
        if isinstance(self.machine.CR, Command):
            return (
                f"{self.machine.AR} - "
                f"{self.machine.CR.toHexCode()} - "
                f"{self.machine.CR.toString()}"
            )

        return "0"

    def now(self):
        return self.tick

    def instruction_fetch_stage(self):
        self.machine.load_ip()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_br()
        self.machine.latch_ar()
        self.tick_(info="INSTRUCTION FETCH; ")

        self.machine.read(self.tick_, self.now)

        self.machine.latch_cr()
        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.inc()
        self.machine.latch_ip()
        self.tick_(info="INSTRUCTION FETCH; ")

        print(self.machine.CR.op_code)
        print(self.machine.CR.addr_mode)
        print(self.machine.CR.arg)

        self.instructions.append(f"{self.machine.AR} - {self.machine.CR.toHexCode()} - {self.machine.CR.toString()}")

    def operand_fetch_stage(self):
        print(self.machine.CR)
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
        self.tick_(info=f"IN {port}; ")

        self.machine.in_()
        self.tick_(info=f"IN {port}; ")

    def out(self):
        port = self.machine.CR.arg
        self.machine.out()
        self.tick_(info=f"OUT {port}; ")

        self.machine.io_controller.out(port)
        self.tick_(info=f"OUT {port}; ")

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
        self.machine.latch_ac()
        self.tick_()

    def inc_sp(self):
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
        self.machine.latch_ps_flags()
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
        self.machine.load_left_zero()
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
        self.tick_(info="HANDLE INTERRUPT; ")

        self.machine.load_sp()
        self.machine.load_left_zero()
        self.machine.alu.invert_left()
        self.machine.alu.sum()
        self.machine.latch_sp()
        self.machine.latch_ar()
        self.tick_(info="HANDLE INTERRUPT; ")

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
        self.tick_(info="HANDLE INTERRUPT; ")

        self.machine.write(self.tick_, self.now)

        self.machine.PS |= 0x20

        self.machine.latch_iport()
        self.machine.load_br()
        self.machine.load_right_zero()
        self.machine.alu.sum()
        self.machine.latch_ar()
        self.tick_(info="HANDLE INTERRUPT; ")

        self.machine.read(self.tick_, self.now)
        self.machine.DR_selector = False
        self.machine.latch_dr()
        self.tick_(info="HANDLE INTERRUPT; ")

        self.machine.load_dr()
        self.machine.load_left_zero()
        self.machine.alu.sum()
        self.machine.latch_ip()
        self.tick_(info="HANDLE INTERRUPT; ")


        self.machine.io_controller.IREQ = False


    def cycle(self):
        self.instruction_fetch_stage()
        self.operand_fetch_stage()
        self.execute_stage()
        self.interrupt_stage()