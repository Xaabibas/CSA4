import sys

from Machine import ControlUnit
from Lexer import Lexer
from Analyzer import Analyzer
from AST import Parser
from CodeGerator import CodeGenerator


class Translator:
    def __init__(self, source, dest_file):
        self.source = source
        self.code = []
        self.global_ = []
        self.dest_file = dest_file

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
        self.generate_file()

    def generate_file(self):
        with open(self.dest_file, "wb") as file:
            for c in self.code:
                file.write(c.toBytes())


if __name__ == "__main__":
    _, source_file, dest_file = sys.argv
    stdlib = open("stdlib")
    content = stdlib.read()
    stdlib.close()

    source = open(source_file)
    program = source.read()
    source.close()

    program = content + "\n" + program

    translator = Translator(program, dest_file)
    translator.translate()
