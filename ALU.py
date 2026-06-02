from CommandTypes import Command
from MagicNumber import MagicNumber


class ALU:
    N: int = 0
    Z: int = 1
    V: int = 0
    C: int = 0
    right: int | Command = 0
    left: int | Command = 0
    one: int = 1
    out: int | Command = 0

    def to_int(self):
        if isinstance(self.right, Command):
            self.right = self.right.to_int()
        if isinstance(self.left, Command):
            self.left = self.left.to_int()
        self.right = self.right & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.left = self.left & (2 ** MagicNumber.WORD_LEN.value - 1)

    def set_nz(self):
        self.N = (self.out >> (MagicNumber.WORD_LEN.value - 1)) & 1
        self.Z = 1 if self.out == 0 else 0

    def set_vc(self):
        self.V = 1 if (self.right > 0 and self.left > 0 and self.out < 0) or (self.right < 0 and self.left < 0 and self.out > 0) else 0
        self.C = (self.out >> MagicNumber.WORD_LEN.value) & 0x1

    def invert_right(self):
        self.to_int()
        self.right = ~self.right

    def invert_left(self):
        self.to_int()
        self.left = ~self.left

    def sum(self):
        self.to_int()
        self.out = self.left + self.right
        self.set_vc()
        self.out = self.out & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def inc(self):
        self.to_int()
        self.out = self.left + self.right + self.one
        self.set_vc()
        self.out = self.out & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def adc(self, carry):
        self.to_int()
        self.out = self.left + self.right + carry
        self.set_vc()
        self.out = self.out  & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def mul(self):
        self.to_int()
        self.out = (self.left * self.right) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def div(self):
        self.to_int()
        self.out = (self.left // self.right) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def mod(self):
        self.to_int()
        self.out = (self.left % self.right) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def and_(self):
        self.to_int()
        self.out = self.left & self.right
        self.set_nz()

    def extend(self):
        self.out = self.right.arg
