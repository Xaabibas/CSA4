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

    def toInt(self):
        if isinstance(self.right, Command):
            self.right = self.right.toInt()
        if isinstance(self.left, Command):
            self.left = self.left.toInt()

    def set_nz(self):
        self.N = (self.out >> (MagicNumber.WORD_LEN.value - 1)) & 1
        self.Z = 1 if self.out == 0 else 0

    def set_vc(self):
        self.V = 1 if (self.right > 0 and self.left > 0 and self.out < 0) or (self.right < 0 and self.left < 0 and self.out > 0) else 0
        self.C = ((self.left & (2 ** MagicNumber.WORD_LEN.value - 1)) +
                  (self.right & (2 ** MagicNumber.WORD_LEN.value - 1)
                                                                           ) >> MagicNumber.WORD_LEN.value) & 0x1

    def invert_right(self):
        self.toInt()
        self.right = ~self.right

    def invert_left(self):
        self.toInt()
        self.left = ~self.left

    def sum(self):
        self.toInt()
        self.out = (self.left + self.right) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()
        self.set_vc()

    def inc(self):
        self.toInt()
        self.out = (self.left + self.right + self.one) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()
        self.set_vc()

    def mul(self):
        self.toInt()
        self.out = (self.left * self.right) & (2 ** MagicNumber.WORD_LEN.value - 1)
        self.set_nz()

    def and_(self):
        self.toInt()
        self.out = self.left & self.right
        self.set_nz()

    def extend(self):
        self.out = self.right.arg