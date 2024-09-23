import contextlib
import io
import logging
import os
import tempfile

import machine
import pytest
import translate


@pytest.mark.golden_test("golden/*.yml")
def test_translator_lisp_and_machine(golden, caplog):
    caplog.set_level(logging.DEBUG)
    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source")
        input_stream = os.path.join(tmpdirname, "input")
        target = os.path.join(tmpdirname, "target")
        print("s")

        with open(source, "w", encoding="utf-8") as f:
            f.write(golden["in_source"])
        binary = []
        for c in golden["in_stdin"]:
            binary.append(int(ord(c)))
        with open(input_stream, "wb+") as f:
            for i in binary:
                f.write(i.to_bytes(4, "big"))

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translate.main(source, target)
            print("============================================================")
            machine.main(target, input_stream)


        assert stdout.getvalue() == golden.out["out_stdout"]
