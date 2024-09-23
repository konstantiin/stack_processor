import re
import sys

from isa import Instr, Opcode


class Preprocessor:
    def __init__(self, text) -> None:
        self.text = text

    def check_brackets(self) -> str:
        balance = 0
        for c in self.text:
            if c == "(":
                balance += 1
            elif c == ")":
                balance -= 1
            assert balance >= 0, "missing braces"
        assert balance == 0, "missing braces"

    def remove_comments(self) -> None:
        pattern = r"#[^\n]*$"
        self.text, _ = re.subn(pattern, "", self.text)

    # mooore brackets for parsing convinience)
    def add_brackets(self, text) -> str:
        pattern = r"([a-zA-Z0-9_<=\+\-]+)"
        text, _ = re.subn(pattern, r"(\1)", text)
        # remove double brackets
        pattern = r'\(\(([a-zA-Z0-9_<=\+\-"]+)\)\)'
        text, _ = re.subn(pattern, r"(\1)", text)
        return text

    def remove_spaces(self, text) -> None:
        text, _ = re.subn(r"\s*", "", text)
        return text

    def preprocess(self) -> None:
        self.check_brackets()
        self.remove_comments()
        text = self.text.split('"')
        new_text = []
        assert len(text) % 2 == 1, "string issues.."
        for i, txt in enumerate(text):
            if i % 2 == 0:
                txt = self.add_brackets(txt)
                new_text.append(self.remove_spaces(txt))
            else:
                new_text.append('("' + txt + '")')
        self.text = "".join(new_text)
        return self


"""
everything is a function))
"""
available_functions = {
    "statement-list": -1,
    "string": 1,
    "defun": 3,
    "printi": 1,
    "prints": 1,
    "read": 0,
    "if": 3,
    "setq": 2,
    "loop": -1,
    "when": 2,
    "break": 1,
    "<": 2,
    "<=": 2,
    "+": 2,
    "-": 2,
}

"""
variables and constants are treated like functions with 0 args
"""


class Statement:
    def split_by_brackets(self, text):
        balance = 0
        statement_start = []
        for i, c in enumerate(text):
            if balance == 0:
                statement_start.append(i)
            if c == "(":
                balance += 1
            if c == ")":
                balance -= 1
        statement_start.append(len(text))
        self.tockens = []
        for i in range(1, len(statement_start)):
            statement_text = text[statement_start[i - 1] : statement_start[i]]
            self.tockens.append(statement_text)

    def parse_fargs(self):
        self.func_name = "defun"
        self.params.append(self.tockens[1][1:-1])  # fname
        self.params.append(self.tockens[2][1:-1].split(","))  # params
        txt = "".join(self.tockens[3:])
        self.params.append(Statement().build_from_text(txt))
        available_functions[self.params[0]] = len(self.params[1])

    def convert_tockens_to_statement(self):
        if len(self.tockens) == 1:
            if self.tockens[0][1] == '"' and self.tockens[0][-2] == '"':
                self.func_name = "string"
                self.params.append(self.tockens[0][2:-2])
                return
            if "(" not in self.tockens[0][1:-1]:
                self.func_name = self.tockens[0][1:-1]
                available_functions[self.func_name] = 0
                return
            self.split_by_brackets(self.tockens[0][1:-1])
            if self.tockens[0] == "(defun)":
                self.parse_fargs()
            else:
                self.func_name = self.tockens[0][1:-1]
                for s in self.tockens[1:]:
                    self.params.append(Statement().build_from_text(s))
        else:
            self.func_name = "statement-list"
            for s in self.tockens:
                self.params.append(Statement().build_from_text(s))

    def build_from_text(self, text):
        is_statement = text[0] == "(" and text[-1] == ")"
        assert is_statement, "String " + text + " is not a lisp statement"

        self.split_by_brackets(text)
        self.convert_tockens_to_statement()
        assert available_functions[self.func_name] == -1 or available_functions[self.func_name] == len(self.params), (
            self.func_name
            + " accept "
            + str(available_functions[self.func_name])
            + " but "
            + str(len(self.params))
            + " found"
        )
        return self

    def __init__(self):
        self.params = []

    def print(self):
        if len(self.params) == 0:
            print(self.func_name, end=" ")
            return
        print(self.func_name + ":{", end="")
        for i in self.params:
            if isinstance(i, Statement):
                i.print()
            else:
                print(i, end="")
        print("}", end="")


custom_funcs_params = {}
custom_funcs_bodies = {}


class Inliner:
    def __init__(self, statement):
        self.root = statement

    def replace_func_vars(self, statement, old_name, new_name):
        assert isinstance(statement, Statement), statement + " is not Statement"
        if statement.func_name == "string":
            return
        if statement.func_name == old_name:
            statement.func_name = new_name
        for s in statement.params:
            self.replace_func_vars(s, old_name, new_name)

    def process_defun_varnames(self):
        for statement in self.root.params:
            if statement.func_name == "defun":
                new_params = []
                for var_name in statement.params[1]:
                    for s in statement.params[2:]:
                        self.replace_func_vars(s, var_name, statement.params[0] + "." + var_name)
                    var = Statement()
                    var.func_name = statement.params[0] + "." + var_name
                    new_params.append(var)
                statement.params[1] = new_params
                custom_funcs_params[statement.params[0]] = statement.params[1]
                custom_funcs_bodies[statement.params[0]] = statement.params[2:]

    def inline_functions(self, statement):
        assert isinstance(statement, Statement), statement + " is not Statement"

        if statement.func_name in custom_funcs_params.keys():
            new_statement = Statement()
            new_statement.func_name = "statement-list"
            for i, arg in enumerate(statement.params):
                init_var = Statement()
                init_var.func_name = "setq"
                var_name = custom_funcs_params[statement.func_name][i]
                init_var.params = [var_name, arg]
                new_statement.params.append(init_var)
            for s in custom_funcs_bodies[statement.func_name]:
                new_statement.params.append(s)
            statement.func_name = new_statement.func_name
            statement.params = new_statement.params
        for s in statement.params:
            if isinstance(s, Statement):
                self.inline_functions(s)

    def inline_and_delete_functions(self):
        self.process_defun_varnames()
        for s in self.root.params:
            self.inline_functions(s)
        new_params = []
        for s in self.root.params:
            if s.func_name != "defun":
                new_params.append(s)
        self.root.params = new_params
        return self


class Faddr:
    def __init__(self, a):
        self.addr = a

    def __iadd__(self, i: int):
        self.addr += i
        return self

    def __str__(self):
        return str(self.addr)


class Mnemcode:
    def __init__(self, addr_start):
        self.addr_start = addr_start
        self.instructions = []

    def concat(self, other):
        offset = len(self.instructions) * 32
        for instruct in other.instructions:
            if isinstance(instruct, list) and isinstance(instruct[1], Faddr):
                instruct[1] += offset
        self.instructions += other.instructions

    def get_end(self):
        return len(self.instructions) * 32

    def append(self, instr, addr=None):
        if addr is not None:
            self.instructions.append([instr, addr])
        else:
            self.instructions.append(instr)


class Encoder:
    def __init__(self, root):
        self.root = root
        self.data_memory = 0x0000000
        self.variables = {}

    def recursive_encoding(self, node):  # noqa C901
        instr = Mnemcode(0)
        match node.func_name:
            case "statement-list":
                for arg in node.params:
                    instr.concat(self.recursive_encoding(arg))
            case "+":
                instr.concat(self.recursive_encoding(node.params[0]))  #    (r1)
                instr.concat(self.recursive_encoding(node.params[1]))  #    (r1,r2)
                instr.append(Instr.add)  #                                      (r1+r2)
            case "-" | "<":
                instr.concat(self.recursive_encoding(node.params[0]))  #    (r1)
                instr.concat(self.recursive_encoding(node.params[1]))  #    (r1,r2)
                instr.append(Instr.sub)  #                                      (r1-r2)
            case "<=":
                instr.concat(self.recursive_encoding(node.params[0]))  #    (r1)
                instr.concat(self.recursive_encoding(node.params[1]))  #    (r1,r2)
                instr.append(Instr.sub)  #                                      (r1 - r2)
                instr.append(Instr.push, 1)  #                                  (r1 - r2, 1)
                instr.append(Instr.sub)  #                                      (r1 - r2 - 1)
            case "read":
                buffer_start = self.data_memory
                self.data_memory += 200 * 32  # buffer capacity - 200
                instr.append(Instr.push, buffer_start)  #                       (buf_start)
                cur_char_ptr = self.data_memory
                self.data_memory += 32
                instr.append(Instr.push, cur_char_ptr)  #                       (buf_start, mem_addr)
                instr.append(Instr.ld)  # saved buffer start                    (buf_start, mem_addr)
                instr.append(Instr.pop)  #                                      (buf_start)
                instr.append(Instr.pop)  #                                      ()
                loop_start = Faddr(instr.get_end())
                instr.append(Instr.inp)  #                                       (in)
                instr.append(Instr.push, cur_char_ptr)  #                       (in, mem_addr)
                instr.append(Instr.mov)  #                                      (in, cur_char)
                instr.append(Instr.ld)  # saved char to buf                     (in, cur_char)
                instr.append(Instr.push, 32)  #                                 (in, cur_char, 0x032)
                instr.append(Instr.add)  #                                      (in, cur_char + 32)
                instr.append(Instr.push, cur_char_ptr)  #                       (in, cur_char + 32, mem_addr)
                instr.append(Instr.ld)  #                                       (in, buf_start + 32, mem_addr)
                instr.append(Instr.pop)  #                                      (in, buf_start + 32)
                instr.append(Instr.pop)  #                                      (in)
                instr.append(Instr.jz, loop_start)  #                           () jz decrements tos
                instr.append(Instr.pop)  #                                      ()
                instr.append(Instr.push, buffer_start)  #                       (buf_start)
            case "prints":
                instr.concat(self.recursive_encoding(node.params[0]))  #    (str_start)
                cur_char_ptr = self.data_memory
                instr.append(Instr.push, cur_char_ptr)  #                       (str_start, mem_addr)
                self.data_memory += 32
                instr.append(Instr.ld)  # saved str_start to mem_addr           (str_start, mem_addr)
                instr.append(Instr.pop)  #                                      (str_start)
                instr.append(Instr.pop)  #                                      ()
                loop_start = Faddr(instr.get_end())
                instr.append(Instr.push, cur_char_ptr)  #                       (mem_addr)
                instr.append(Instr.mov)  # pointer to current char              (cur_str)
                instr.append(Instr.mov)  #                                      (char)
                instr.append(Instr.out)  #                                      (char)
                instr.append(Instr.push, cur_char_ptr)  #                       (char,mem_addr)
                instr.append(Instr.mov)  #                                      (char,cur_str)
                instr.append(Instr.push, 32)  #                                 (char,cur_str,0x032)
                instr.append(Instr.add)  #                                      (char,cur_str + 32)
                instr.append(Instr.push, cur_char_ptr)  #                       (char,cur_str+32,mem_addr)
                instr.append(Instr.ld)  #                                       (char,cur_str+32,mem_addr)
                instr.append(Instr.pop)  #                                      (char,cur_str+32)
                instr.append(Instr.pop)  #                                      (char)
                loop_end = Faddr(instr.get_end() + 64)
                instr.append(Instr.jz, loop_end)  #                           ()
                instr.append(Instr.jump, loop_start)  #                         ()
            case "printi":
                instr.concat(self.recursive_encoding(node.params[0]))  #    (r1)
                instr.append(Instr.out)  #                                      (r1)
                instr.append(Instr.pop)  #                                      ()
            case "string":
                buffer_start = self.data_memory
                next_char_addr = buffer_start
                for c in node.params[0]:
                    instr.append(Instr.push, ord(c))  #                         (char)
                    instr.append(Instr.push, next_char_addr)  #                 (char, mem_addr)
                    instr.append(Instr.ld)  #                                   (char, mem_addr)
                    instr.append(Instr.pop)  #                                  (char)
                    instr.append(Instr.pop)  #                                  ()
                    next_char_addr += 32
                instr.append(Instr.push, 0)  #                                  (null)
                instr.append(Instr.push, next_char_addr)  #                     (null, mem_addr)
                instr.append(Instr.ld)  #                                       (null, mem_addr)
                instr.append(Instr.pop)  #                                      (null)
                instr.append(Instr.pop)  #                                      ()
                instr.append(Instr.push, buffer_start)  #                       (str_start)
                self.data_memory = next_char_addr + 32
            case "setq":
                instr.concat(self.recursive_encoding(node.params[1]))  #    (value)
                if node.params[0].func_name in self.variables.keys():
                    var_addr = self.variables[node.params[0].func_name]
                else:
                    var_addr = self.data_memory
                    self.data_memory += 32
                instr.append(Instr.push, var_addr)  #                           (value, addr)
                instr.append(Instr.ld)  #                                       (value, addr)
                instr.append(Instr.pop)  #                                      (value)
                instr.append(Instr.pop)  #                                      ()
                self.variables[node.params[0].func_name] = var_addr
            case "if":
                cond = self.recursive_encoding(node.params[0])
                is_true = self.recursive_encoding(node.params[1])
                is_false = self.recursive_encoding(node.params[2])
                instr.concat(cond)  #           s if cond==true             (cond)
                false_addr = instr.get_end() + 32 + is_true.get_end() + 32
                endif_addr = instr.get_end() + 32 + is_true.get_end() + 32 + is_false.get_end()
                print(false_addr, endif_addr)
                instr.append(Instr.jns, Faddr(false_addr))  #                   ()
                instr.concat(is_true)  #                                    (rt)
                instr.append(Instr.jump, Faddr(endif_addr))  #                  (rt)
                instr.concat(is_false)  #                                   (rf)
            case "when":
                cond = self.recursive_encoding(node.params[0])
                is_true = self.recursive_encoding(node.params[1])
                instr.concat(cond)  #        s if cond==true                (cond)
                endif_addr = instr.get_end() + 32 + is_true.get_end()
                print(endif_addr)
                instr.append(Instr.jns, Faddr(endif_addr))  #                   ()
                instr.concat(is_true)  #                                    (rt)
            case "break":
                instr.append(Instr.jump, "unknown")  #                          ()
            case "loop":
                for arg in node.params:
                    instr.concat(self.recursive_encoding(arg))
                instr.append(Instr.jump, Faddr(0))  # loop starts at 0          (0)
                end_addr = Faddr(instr.get_end())
                for instruct in instr.instructions:
                    if isinstance(instruct, list) and instruct[1] == "unknown":
                        instruct[1] = end_addr
            case _:
                if re.search(r"[a-zA-Z_]", node.func_name):
                    assert node.func_name in self.variables.keys(), node.func_name + " not variable"
                    instr.append(Instr.push, self.variables[node.func_name])  # (addr)
                    instr.append(Instr.mov)  #                                  (value)
                else:
                    instr.append(Instr.push, int(node.func_name))  #            (const)
        return instr

    def make_code(self):
        code = self.recursive_encoding(self.root)
        for instr in code.instructions:
            if isinstance(instr, list) and isinstance(instr[1], Faddr):
                instr[1] = instr[1].addr
        return code


def translate(text):
    preprocessor = Preprocessor(text).preprocess()
    root = Statement().build_from_text(preprocessor.text)
    inliner = Inliner(root).inline_and_delete_functions()  # recursion is not supported))
    encoder = Encoder(inliner.root)
    code = encoder.make_code()  # mnemonic code
    return Opcode(code.instructions)


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    code.save_code(target)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translate.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
