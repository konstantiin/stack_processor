import sys
from enum import Enum, auto

from isa import read_code


class Writer:
    def __init__(self, path) -> None:
        self.path = path

    def send(self, bytes4):
        with open(self.path, "wb") as f:
            f.write(bytes4.to_bytes(4, "big"))

class Reader:
    def __init__(self, path) -> None:
        self.path = path
        self.bytes = []
        with open("myfile", "rb") as f:
            byte = f.read(1)
            while bytes != b"":
                self.bytes.append(byte)
                byte = f.read(1)

    def receive(self):
        b = self.bytes[0]
        self.bytes = self.bytes[1:]
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

class Alu(Enum):
    PLUS = auto()
    MINUS = auto()

class Ip(Enum):
    INC = auto()
    ADDR = auto()

class DataPath:
    def __init__(self, writer, reader):
        self.sp = 0
        self.stack = [0]*50
        self.tos = 0
        self.alu_res = 0
        self.mem_read = 0
        self.input = 0
        self.instr_arg = 0
        self.sel_sp = 0
        self.sel_tos = 0
        self.sel_alu = 0
        self.data_memory = {}
        self.writer = writer
        self.reader = reader

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
                self.alu_res = self.stack[self.sp-1] + self.tos
            case Alu.MINUS:
                self.alu_res = self.stack[self.sp-1] - self.tos
            case _:
                raise ValueError
    def latch_st(self):
        self.stack[self.sp+1] = self.tos

    def latch_tos(self):
        match self.sel_tos:
            case Tos.STACK:
                self.tos = self.stack[self.sp]
            case Tos.ALU:
                self.tos = self.alu
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
        self.data_memory[self.tos] = self.stack[self.sp-1]

    def inp(self):
        self.input = self.reader.receive()

    def out(self):
        self.writer.send(self.tos)


class ControlUnit:
    def __init__(self, program, writer, reader):
        self.data_memory = program
        self.ip = 0
        self.sel_ip = "inc"
        self.addr = 0
        self.machine = DataPath(writer, reader)
        self.tick = 0

    def latch_ip(self):
        match self.sel_ip:
            case Ip.INC:
                self.ip+=1
            case Ip.ADDR:
                self.ip = self.s
            case _:
                raise ValueError
    def tick(self, signals):
        self.tick += 1

    def decode(self):
        arg = self.data_memory[self.ip] & ((1<<28)-1)
        instr = self.data_memory[self.ip] & (15 << 28)
        match instr:
            case 0: #hlt
                return False
            case 1: #push
                self.machine.instr_arg = arg
                self.machine.sel_tos = Tos.CONTROL
                self.machine.sel_sp = Sp.INC
                self.machine.latch_tos()
                self.machine.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.machine.latch_st()
                self.latch_ip()
                self.tick()
            case 2: #pop
                self.machine.sel_sp = Sp.DEC
                self.machine.latch_sp()
                self.tick()
                self.machine.sel_tos = Tos.STACK
                self.sel_ip = Ip.INC
                self.machine.latch_tos()
                self.latch_ip()
                self.tick()
            case 3: #mov
                self.machine.sel_tos = Tos.DATA
                self.machine.read_mem()
                self.machine.latch_tos()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.tick()
            case 4: #ld
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.machine.wrtite_mem()
                self.tick()
            case 5: #out
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.machine.out()
                self.tick()
            case 6: #in
                self.machine.sel_tos = Tos.IN
                self.machine.sel_sp = Sp.inc
                self.machine.inp()
                self.machine.sel_tos()
                self.machine.latch_sp()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.machine.latch_st()
                self.tick()
            case 7: #jns
                ip = Ip.INC
                if self.machine.tos >= 0:
                    ip = Ip.ADDR
                self.addr = arg
                self.sel_ip = ip
                self.latch_ip()
                self.tick()
            case 8: #jz
                ip = Ip.INC
                if self.machine.tos == 0:
                    ip = Ip.ADDR
                self.addr = arg
                self.sel_ip = ip
                self.latch_ip()
                self.tick()
            case 9: #jump
                self.sel_ip = Ip.ADDR
                self.addr = arg
                self.latch_ip()
                self.tick()
            case 10: #add
                self.machine.sel_alu = Alu.PLUS
                self.sel_tos = Tos.Alu
                self.machine.sel_sp = Sp.DEC
                self.machine.latch_tos()
                self.machine.alu()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.machine.latch_st()
                self.tick()
            case 11: #sub
                self.machine.sel_alu = Alu.MINUS
                self.sel_tos = Tos.Alu
                self.machine.sel_sp = Sp.DEC
                self.machine.latch_tos()
                self.machine.alu()
                self.tick()
                self.sel_ip = Ip.INC
                self.latch_ip()
                self.machine.latch_st()
                self.tick()
            case _:
                raise ValueError
        return True
    def emulate(self):
        should_continue = True
        while(should_continue):
            try:
                should_continue = self.decode()
            except ValueError:
                #log.error
                return
            self.log()


def main(program):
    instructions = read_code(program)
    model = ControlUnit(instructions, Writer("iostreams/in"), Reader("iostreams/out"))
    model.emulate()

if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file>"
    _, program = sys.argv
    main(program)
