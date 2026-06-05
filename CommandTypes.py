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
    ADC = 0x43
    DIV = 0x44
    MOD = 0x45

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
    INDIRECT = 0xA

    IMMEDIATE = 0xF


@dataclass
class Command:
    name: str
    op_code: OpCode
    addr_mode: AddrMode
    arg: int

    def __init__(self, op_code: OpCode, addr_mode: AddrMode, arg: int):
        self.op_code = op_code
        self.addr_mode = addr_mode
        self.arg = arg

    def to_string(self):
        string = self.op_code.name
        if self.op_code.value & 0xF0 != 0:
            if self.addr_mode == AddrMode.DIRECT:
                string += f" {self.arg}"
            elif self.addr_mode == AddrMode.RELATIVE_SP:
                string += f" &({self.arg})"
            elif self.addr_mode == AddrMode.RELATIVE_IP:
                string += f" ({self.arg})"
            elif self.addr_mode == AddrMode.INDIRECT:
                string += f" (({self.arg}))"
            else:
                string += f" #{self.arg}"
        return string

    def __str__(self):
        return self.to_string()

    def __format__(self, format_spec):
        return format(self.to_int(), format_spec)

    def to_int(self):
        return (
            (self.op_code.value << MagicNumber.OP_CODE_POS.value)
            + (self.addr_mode.value << MagicNumber.ADDR_POS.value)
            + self.arg
        ) & (2**MagicNumber.WORD_LEN.value - 1)

    def to_hex_code(self):
        command_bytes = self.to_int().to_bytes(MagicNumber.WORD_LEN.value // 8, "little", signed=True)

        hex_code = "0x"
        for byte in reversed(command_bytes):
            hex_code += hex(byte)[2:].rjust(2, "0")

        return hex_code

    def to_bytes(self):
        return self.to_int().to_bytes(MagicNumber.WORD_LEN.value // 8, "little", signed=True)


def decode(code):
    op_code = OpCode(code >> 24)
    try:
        addr_mode = AddrMode((code & 0x00F00000) >> 20)
    except Exception:
        addr_mode = AddrMode.DIRECT
    arg = code & 0x000FFFFF

    return Command(op_code, addr_mode, arg)


def read_commands_from_file(filename):
    code = []

    with open(filename, "rb") as file:
        data = file.read()

        size = MagicNumber.WORD_LEN.value // 8

        for i in range(0, len(data), size):
            command_bytes = data[i : i + size]

            command_int = int.from_bytes(command_bytes, "little", signed=True)

            command = decode(command_int)

            code.append(command)

    return code
