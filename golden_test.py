import contextlib
import io
import logging
import os
import tempfile

import machine
import pytest
import translator
from pathlib import Path


def TDirectory():
    dir_name = "/test/" + str(random.randint(100, 999))
    Path(dir_name).mkdir(parents=True, exist_ok=True)


@pytest.mark.golden_test("golden/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with TDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source")
        input_stream = os.path.join(tmpdirname, "input")
        target_data = os.path.join(tmpdirname, "target_data")
        target_code = os.path.join(tmpdirname, "target_code")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target_data, target_code)
            print("============================================================")
            machine.main(target_code, target_data, input_stream)

        with open(target_code, mode="rb") as file:
            code = file.read()

        with open(target_data, mode="rb") as file:
            data = file.read()

        formatted_code = ""
        for x in read_code(target_code):
            formatted_code += str(x) + "\n"

        formatted_data = str(read_data(target_data))

        assert data == golden.out["out_data"]
        assert code == golden.out["out_code"]
        assert formatted_code == golden.out["out_formatted_code"]
        assert formatted_data == golden.out["out_formatted_data"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
