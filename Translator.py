import sys

from Analyzer import Analyzer
from AST import Parser
from CodeGerator import CodeGenerator
from Lexer import Lexer
from MagicNumber import MagicNumber


class Translator:
    def __init__(self, source_file, dest_file, memory_file, debug_file):
        stdlib = open("stdlib")
        content = stdlib.read()
        stdlib.close()

        source = open(source_file)
        program = source.read()
        source.close()

        program = content + "\n" + program

        self.source = program
        self.dest_file = dest_file
        self.debug_file = debug_file
        self.memory_file = memory_file

    def translate(self):
        lexer = Lexer(self.source)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse_program()

        analyzer = Analyzer()
        analyzer.analyze(ast)

        generator = CodeGenerator()
        generator.generate(ast)

        code = generator.code
        memory = generator.memory

        if self.debug_file is not None:
            with open(self.debug_file, "w") as file:

                file.write("CODE:\n")
                for i, c in enumerate(code):
                    file.write(f" {i + MagicNumber.START_IP.value:07} - {c.to_hex_code()} - {c}\n")

                file.write("DATA:\n")
                for i, d in memory.items():
                    file.write(f" {i:07}: {d:010}\n")

        self.generate_binary_file(code)
        self.generate_memory_file(memory)

    def generate_binary_file(self, code):
        with open(self.dest_file, "wb") as file:
            for c in code:
                file.write(c.to_bytes())

    def generate_memory_file(self, memory):
        with open(self.memory_file, "w") as file:
            file.write(repr(memory))


if __name__ == "__main__":
    assert 4 <= len(sys.argv) <= 5, "Wrong argument count: python Translator.py <source_file> <dest_file> <memory_file> [<debug_file>] "

    if len(sys.argv) == 4:
        _, source_file, dest_file, memory_file = sys.argv
        debug_file = None
    else:
        _, source_file, dest_file, memory_file, debug_file = sys.argv

    translator = Translator(source_file, dest_file, memory_file, debug_file)
    translator.translate()
