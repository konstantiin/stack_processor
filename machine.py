import logging
import sys
from enum import Enum, auto

from isa import Instr, read_code


class Writer:
    def __init__(self):
        self.buf = ""

    def outc(self, c):
        # don't print special character for testing
        if c == 0:
            return
        self.buf += chr(c)

    def outi(self, i):
        self.buf += "<" + str(i) + ">"


class Reader:
    def __init__(self, path) -> None:
        self.path = path
        self.data = []
        with open(self.path, "rb") as f:
            byte = f.read(1)
            while byte != b"":
                self.data.append(int.from_bytes(byte, "big"))
                byte = f.read(1)
        self.data.append(0)

    def receive(self):
        b = self.data[0]
        self.data = self.data[1:]
        return b


class Tos(Enum):
    STACK = auto()
    ALU = auto()
    DATA = auto()
    INPUT = auto()
    CONTROL = auto()


class Sp(Enum):
    INC = auto()
    DEC = auto()
    MUL = auto()


class Alu(Enum):
    PLUS = auto()
    MINUS = auto()
    MUL = auto()


class Ip(Enum):
    INC = auto()
    ADDR = auto()


class DataPath:
    def __init__(self, writer, reader):
        self.sp = 0
        self.stack = [0] * 50
        self.tos = 0
        self.alu_res = 0
        self.mem_read = 0
        self.input = 0
        self.instr_arg = 0
        self.sel_sp = 0
        self.sel_tos = 0
        self.sel_alu = 0
        self.data_memory = {}
        self.reader = reader
        self.writer = writer

    def latch_sp(self):
        match self.sel_sp:
            case Sp.INC:
                self.sp += 1
            case Sp.DEC:
                self.sp -= 1
            case _:
                raise ValueError

    def alu(self):
        match self.sel_alu:
            case Alu.PLUS:
                self.alu_res = self.stack[self.sp - 1] + self.tos
            case Alu.MINUS:
                self.alu_res = self.stack[self.sp - 1] - self.tos
            case Alu.MUL:
                self.alu_res = self.stack[self.sp - 1] * self.tos
            case _:
                raise ValueError

    def latch_st(self):
        self.stack[self.sp] = self.tos

    def latch_tos(self):
        match self.sel_tos:
            case Tos.STACK:
                self.tos = self.stack[self.sp]
            case Tos.ALU:
                self.tos = self.alu_res
            case Tos.DATA:
                self.tos = self.mem_read
            case Tos.INPUT:
                self.tos = self.input
            case Tos.CONTROL:
                self.tos = self.instr_arg
            case _:
                raise ValueError

    def read_mem(self):
        self.mem_read = self.data_memory[self.tos]

    def wrtite_mem(self):
        self.data_memory[self.tos] = self.stack[self.sp - 1]

    def inp(self):
        self.input = self.reader.receive()

    def outc(self):
        self.writer.outc(self.tos)

    def outi(self):
        self.writer.outi(self.tos)


class ControlUnit:
    def __init__(self, program, writer, reader):
        self.ip = 0
        self.sel_ip = "inc"
        self.addr = 0
        self.data_path = DataPath(writer, reader)
        self._tick = 0
        self.instr_memory = {}
        addr = 0
        for i, instr in enumerate(program):
            self.instr_memory[i * 32] = instr
            addr = i
        addr += 1
        self.instr_memory[addr * 32] = 0

    def latch_ip(self):
        match self.sel_ip:
            case Ip.INC:
                self.ip += 32
            case Ip.ADDR:
                self.ip = self.addr
            case _:
                raise ValueError

    def tick(self):
        self._tick += 1

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        i = Instr((self.instr_memory[self.ip] & (15 << 28)) >> 28).name
        return "TICK: {:3d} IP: {:5d} TOS: {:9d} STACK[SP]: {:9d} STACK[SP-1]: {:9d} SP: {:3d} INSTR: {:5s} ARG: {:9d}".format(
            self._tick,
            self.ip,
            self.data_path.tos,
            self.data_path.stack[self.data_path.sp],
            self.data_path.stack[self.data_path.sp - 1],
            self.data_path.sp,
            str(i),
            self.instr_memory[self.ip] & ((1 << 28) - 1),
        )

    def decode(self):
        arg = self.instr_memory[self.ip] & ((1 << 28) - 1)
        instr = (self.instr_memory[self.ip] & (15 << 28)) >> 28
        logging.debug("%s", self)
        match instr:
            case 0:  # hlt
                return False
            case 1:  # push
                self.data_path.instr_arg = arg
                self.data_path.sel_tos = Tos.CONTROL
                self.data_path.sel_sp = Sp.INC
                self.data_path.latch_tos()
                self.data_path.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.data_path.latch_st()
                self.latch_ip()
                self.tick()
            case 2:  # pop
                self.data_path.sel_sp = Sp.DEC
                self.data_path.latch_sp()
                self.tick()
                self.data_path.sel_tos = Tos.STACK
                self.sel_ip = Ip.INC
                self.data_path.latch_tos()
                self.latch_ip()
                self.tick()
            case 3:  # mov
                self.data_path.sel_tos = Tos.DATA
                self.data_path.read_mem()
                self.data_path.latch_tos()
                self.tick()
                self.data_path.latch_st()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.tick()
            case 4:  # ld
                self.data_path.wrtite_mem()
                self.data_path.sel_sp = Sp.DEC
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.sel_tos = Tos.STACK
                self.data_path.latch_tos()
                self.tick()
            case 5:  # outc
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.outc()
                self.tick()
            case 6:  # outi
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.outi()
                self.tick()
            case 7:  # in
                self.data_path.sel_tos = Tos.INPUT
                self.data_path.sel_sp = Sp.INC
                self.data_path.inp()
                self.data_path.latch_tos()
                self.data_path.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.latch_st()
                self.tick()
            case 8:  # jns
                ip = Ip.INC
                if self.data_path.tos >= 0:
                    ip = Ip.ADDR
                self.addr = arg
                self.data_path.sel_sp = Sp.DEC
                self.data_path.latch_sp()
                self.tick()
                self.data_path.sel_tos = Tos.STACK
                self.data_path.latch_tos()
                self.sel_ip = ip
                self.latch_ip()
                self.tick()
            case 9:  # jz
                ip = Ip.INC
                if self.data_path.tos == 0:
                    ip = Ip.ADDR
                self.addr = arg
                self.data_path.sel_sp = Sp.DEC
                self.data_path.latch_sp()
                self.tick()
                self.data_path.sel_tos = Tos.STACK
                self.data_path.latch_tos()
                self.sel_ip = ip
                self.latch_ip()
                self.tick()
            case 10:  # jump
                self.sel_ip = Ip.ADDR
                self.addr = arg
                self.latch_ip()
                self.tick()
            case 11:  # add
                self.data_path.sel_alu = Alu.PLUS
                self.data_path.sel_tos = Tos.ALU
                self.data_path.sel_sp = Sp.DEC
                self.data_path.alu()
                self.data_path.latch_tos()
                self.data_path.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.latch_st()
                self.tick()
            case 12:  # sub
                self.data_path.sel_alu = Alu.MINUS
                self.data_path.sel_tos = Tos.ALU
                self.data_path.sel_sp = Sp.DEC
                self.data_path.alu()
                self.data_path.latch_tos()
                self.data_path.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.latch_st()
                self.tick()
            case 13:  # mul
                self.data_path.sel_alu = Alu.MUL
                self.data_path.sel_tos = Tos.ALU
                self.data_path.sel_sp = Sp.DEC
                self.data_path.alu()
                self.data_path.latch_tos()
                self.data_path.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.data_path.latch_st()
                self.tick()
            case _:
                logging.error("Wrong instruction")
                return False
        return True

    def emulate(self):
        should_continue = True
        logging.debug("%s", "started emeulation")
        while should_continue:
            should_continue = self.decode()


def main(program, input_stream):
    instructions = read_code(program)
    model = ControlUnit(instructions, Writer(), Reader(input_stream))
    model.emulate()
    print(model.data_path.writer.buf, end="")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_stream>"
    _, program, input_stream = sys.argv
    main(program, input_stream)
