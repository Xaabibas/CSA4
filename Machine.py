from collections.abc import Callable

from ALU import ALU
from CommandTypes import Command
from MagicNumber import MagicNumber
from Memory import Memory
from External import IOController


class Machine:
    alu: ALU = ALU()
    memory: Memory
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
    DR_selector: bool = True # True - alu; False - memory

    def __init__(self, memory):
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
        self.PS = self.alu.out & (2 ** MagicNumber.PS_LEN.value - 1)

    def latch_ps_flags(self):
        NZVC = (self.alu.N << 3) | (self.alu.Z << 2) | (self.alu.V << 1) | self.alu.C
        self.PS = (self.PS & 0x30) | NZVC

    def ei(self):
        self.PS = self.PS | 0x10

    def di(self):
        self.PS = self.PS & 0x2F

    def latch_ar(self):
        self.AR = self.alu.out & (2 ** MagicNumber.ADDR_LEN.value - 1)

    def latch_ip(self):
        self.IP = self.alu.out

    def latch_cr(self):
        self.CR = self.memory_bus

    def latch_sp(self):
        self.SP = self.alu.out

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