from lark import Lark, Token, Tree
import math
import ast

l = Lark(
    r"""
start: (orstmt | andstmt | _NL)*
orstmt: IDENTIFIER ":" atom ("|" atom)+ "\n"
andstmt: IDENTIFIER ":" atom ("&" atom)+ "\n"
IDENTIFIER: WORD
atom: STRING | TRUE | FALSE
TRUE: "true"
FALSE: "false"
_NL: /(\r?\n)+\s*/

%import common.WORD
_STRING_INNER: /.*?/
_STRING_ESC_INNER: _STRING_INNER /(?<!\\)(\\\\)*?/ 
STRING : "\"" _STRING_ESC_INNER "\"" | "'" _STRING_ESC_INNER "'"

%ignore " "
"""
)


def mogrify_atom(a):
    if isinstance(a, Token):
        if a.type == "STRING":
            return ast.literal_eval(a.value)
        elif a.type == "TRUE":
            return True
        elif a.type == "FALSE":
            return False
    raise NotImplementedError(str(stmt))


with open("grammar.txt", "r") as infp:
    root = l.parse(infp.read())

fields = []

for stmt in root.children:
    if stmt.data in ("orstmt", "andstmt"):
        identifier = str(next(stmt.scan_values(lambda c: c.type == "IDENTIFIER")))
        atoms = [a.children[0] for a in stmt.find_data("atom")]
        atoms = [mogrify_atom(a) for a in atoms]
        fields.append((identifier, ("|" if stmt.data == "orstmt" else "&"), atoms))
    else:
        raise NotImplementedError(str(stmt))

total_bits = 0
for identifier, op, options in fields:
    if op == "&":
        bits = len(options)
        description = f"{bits}-bit bitfield"
    elif op == "|":
        bits = math.ceil(math.log2(len(options)))
        description = f"{bits}-bit enum"
    print(f"{identifier:15}: {description} ({len(options)} options)")
    total_bits += bits

print(f"Total bits: {total_bits}")
