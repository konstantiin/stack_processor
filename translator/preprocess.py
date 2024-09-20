import re


def remove_spaces(text):
    # open bracket
    text, _ = re.subn(r"\s*\(\s*", r"(", text)
    # close bracket
    text, _ = re.subn(r"\s*\)\s*", r")", text)
    return text


# mooore brackets for parsing convinience)
def add_brackets(text):
    pattern = r"([a-zA-Z0-9_<=\+\-]+)"
    text, _ = re.subn(pattern, r"(\1)", text)
    # remove double brackets
    pattern = r'\(\(([a-zA-Z0-9_<=\+\-"]+)\)\)'
    text, _ = re.subn(pattern, r"(\1)", text)
    return text


def remove_comments(text):
    pattern = r"#[^\n]*$"
    text, _ = re.subn(pattern, "", text)
    return text


def remove_spaces(text):
    text, _ = re.subn("\s*", "", text)
    return text


def check_braces(text):
    balance = 0
    for c in text:
        if c == "(":
            balance += 1
        elif c == ")":
            balance -= 1
        assert balance >= 0, "missing braces"
    assert balance == 0, "missing braces"


def preprocess(text):
    check_braces(text)
    text = remove_comments(text)
    text = text.split('"')
    new_text = []
    assert len(text) % 2 == 1, "string issues.."
    for i, txt in enumerate(text):
        if i % 2 == 0:
            txt = add_brackets(txt)
            new_text.append(remove_spaces(txt))
        else:
            new_text.append('("' + txt + '")')
    text = "".join(new_text)
    return text
