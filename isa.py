from enum import IntEnum, auto


class Instr(IntEnum):
    hlt = 0
    push = auto()
    pop = auto()
    mov = auto()
    ld = auto()
    out = auto()
    inp = auto()
    jns = auto()
    jz = auto()
    jump = auto()
    add = auto()
    sub = auto()
class Opcode:

    def __init__(self, mnemonics):
        self.binary = []
        for instr in mnemonics:
            if isinstance(instr, list):
                self.binary.append((instr[0] << 28) + instr[1])
            else:
                self.binary.append(instr << 28)

    def save_code(self, path):
        with open(path, "wb") as f:
            for i in self.binary:
                f.write(i.to_bytes(4, "big"))

def read_code(path):
    instructions = []
    with open(path, "rb") as f:
        bytes4 = f.read(4)
        while bytes4 != b"":
            instructions.append(bytes4)
            bytes4 = f.read(4)
    return instructions
