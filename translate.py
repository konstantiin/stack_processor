import re
import sys
from translator.statement import Statement
from translator.inliner import Inliner
from translator.encoder import Encoder
import translator.preprocess as preprocess


def translate(text):
    text = preprocess.preprocess(text)
    print(text)
    root = Statement().build_from_text(text)
    root.print()
    inliner = Inliner(root)
    inliner.inline_and_delete_functions()
    encoder = Encoder(inliner.root)
    encoder.make_code()
    return encoder.mnemcode.instructions


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)

    for i in code:
        print(i)
    # write_code(target, code)
    # print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator/translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
