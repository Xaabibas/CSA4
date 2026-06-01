from ControlUnit import ControlUnit
from Lexer import Lexer
from Analyzer import Analyzer
from AST import Parser
from CodeGerator import CodeGenerator


class Translator:
    def __init__(self, source: str, file):
        self.source = source
        self.code = []
        self.global_ = []
        self.cu = ControlUnit(file)

    def translate(self):
        lexer = Lexer(self.source)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse_program()

        analyzer = Analyzer()
        analyzer.analyze(ast)

        generator = CodeGenerator()
        generator.generate(ast)

        self.code = generator.code
        self.global_ = generator.global_

        print(generator.variables)

    def load(self, start=512):
        for addr, command in enumerate(self.code):
            self.cu.memory.memory[addr + start] = command
        for port, handle_addr in self.global_:
            self.cu.memory.memory[port] = handle_addr
        self.cu.machine.IP = start

        return self.cu

def run(cu: ControlUnit, limit: int):
    try:
        for _ in range(limit):
            cu.cycle()
        else:
            raise Exception("Op limit")
    except SystemExit:
        for i in range(3):
            print(cu.memory.memory.get(128 + i, 0))



if __name__ == "__main__":
    ex = """
    func fact(a) {
        if (a <= 1) {
            return 1;
        }
        return a * fact(a - 1);
    }
    var x = 6;

    var z = fact(x);
    """
    with open("debug", "w") as file:
        translator = Translator(ex, file)
        translator.translate()
        cu = translator.load()

        run(cu, 300)

        for i in cu.instructions:
            print(i)