
from translator.lisp_functions import available_functions

numbers = "0123456789"
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
        print(self.tockens)
        if len(self.tockens) == 1:
            if self.tockens[0][1] == '"' and self.tockens[0][-2] == '"':
                self.func_name = "string"
                self.params.append(self.tockens[0][2:-2])
                return
            if "(" not in self.tockens[0][1:-1]:
                self.func_name = self.tockens[0][1:-1]
                print(self.func_name)
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
        assert text[0] == "(" and text[-1] == ")", "String " + text + " is not a lisp statement"
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
