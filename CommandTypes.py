from dataclasses import dataclass
from enum import Enum

from MagicNumber import MagicNumber


class OpCode(Enum):
    # Безадресные команды
    NOP = 0x00
    HALT = 0x01

    IN = 0x02
    OUT = 0x03
    PUSH = 0x04
    POP = 0x05
    INC_SP = 0x0C

    EI = 0x06
    DI = 0x07

    RET = 0x08
    IRET = 0x09

    NEG = 0x0A
    CLR = 0x0B

    # Адресные команды

    LOAD = 0x20
    STR = 0x21

    CALL = 0x30

    ADD = 0x40
    SUB = 0x41
    MUL = 0x42

    AND = 0x50
    OR = 0x51

    COMP = 0x60

    JMP = 0x70
    JEQ = 0x71
    JNE = 0x72
    JMI = 0x73
    JPL = 0x74
    JGE = 0x75
    JLT = 0x76

class AddrMode(Enum):
    DIRECT = 0x0

    RELATIVE_IP = 0x8
    RELATIVE_SP = 0x9
    RELATIVE_INDIRECT = 0xA

    DIRECT_LOAD = 0xF

@dataclass
class Command:
    name: str
    op_code: OpCode
    addr_mode: AddrMode
    arg: int

    def __init__(self, op_code: OpCode, addr_mode:AddrMode, arg: int):
        self.op_code = op_code
        self.addr_mode = addr_mode
        self.arg = arg

    def toString(self):
        string = self.op_code.name
        if self.op_code.value & 0xF0 != 0:
            if self.addr_mode == AddrMode.DIRECT:
                string += f" {self.arg}"
            elif self.addr_mode == AddrMode.RELATIVE_SP:
                string += f" &({self.arg})"
            elif self.addr_mode == AddrMode.RELATIVE_IP:
                string += f" ({self.arg})"
            elif self.addr_mode == AddrMode.RELATIVE_INDIRECT:
                string += f" (({self.arg}))"
            else:
                string += f" #{self.arg}"
        return string

    def __str__(self):
        return str(self.toInt())

    def toInt(self):
        return (((self.op_code.value << MagicNumber.OP_CODE_POS.value) + (self.addr_mode.value << MagicNumber.ADDR_POS.value) + self.arg)
                & (2 ** MagicNumber.WORD_LEN.value - 1))

    def toHexCode(self):
        command_bytes = self.toInt().to_bytes(MagicNumber.WORD_LEN.value // 8, "little", signed=True)

        hex_code = "0x"
        for byte in reversed(command_bytes):
            hex_code += hex(byte)[2:].rjust(2, "0")

        return hex_code
