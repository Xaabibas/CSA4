import contextlib
import io
import os.path
import tempfile

import pytest
from CommandTypes import read_commands_from_file
from Machine import ControlUnit
from Translator import Translator


def normalize_output(text):
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)

@pytest.mark.golden_test("golden/*.yml")
def test(golden):

    with tempfile.TemporaryDirectory() as tmp_dir:

        source_file = os.path.join(tmp_dir, "source")
        binary_file = os.path.join(tmp_dir, "binary")
        memory_file = os.path.join(tmp_dir, "memory")
        input_file = os.path.join(tmp_dir, "input")
        debug_translate_file = os.path.join(tmp_dir, "debug_translate")
        debug_simulate_file = os.path.join(tmp_dir, "debug_simulate")

        with open(source_file, "w", encoding="utf-8") as file:
            file.write(golden["source"])
        with open(input_file, "w", encoding="utf-8") as file:
            file.write(golden["stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator = Translator(source_file, binary_file, memory_file, debug_translate_file)
            translator.translate()

            code = read_commands_from_file(binary_file)

            with open(debug_simulate_file, "w", encoding="utf-8") as debug:
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

        with open(debug_translate_file, encoding="utf-8") as file:
            translate_output = file.read()

        assert normalize_output(translate_output) == normalize_output(golden.out["out_translate"])
        assert normalize_output(stdout.getvalue()) == normalize_output(golden.out["stdout"])
