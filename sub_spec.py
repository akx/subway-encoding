from lark import Lark, Token, Tree
import math
import enum
import ast
import construct
from sub_code import to_shortcode, from_shortcode

GRAMMAR = Lark(
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


def parse_grammar(root):
    for stmt in root.children:
        if stmt.data in ("orstmt", "andstmt"):
            identifier = str(next(stmt.scan_values(lambda c: c.type == "IDENTIFIER")))
            atoms = [a.children[0] for a in stmt.find_data("atom")]
            atoms = [mogrify_atom(a) for a in atoms]
            yield (identifier, ("|" if stmt.data == "orstmt" else "&"), atoms)
        else:
            raise NotImplementedError(str(stmt))


def convert_fields_to_struct_fields(fields, verbose=False):
    total_bits = 0
    struct_fields = []
    for identifier, op, options in fields:
        s_field = None
        if op == "&":
            bits = len(options)
            description = f"{bits}-bit bitfield"
            f_enum = enum.IntFlag(
                identifier, [(op, 1 << i) for (i, op) in enumerate(options)]
            )
            s_field = identifier / construct.FlagsEnum(
                construct.BitsInteger(bits), f_enum
            )
        elif op == "|":
            bits = math.ceil(math.log2(len(options)))
            description = f"{bits}-bit enum"

            if set(options) == {True, False}:
                s_field = identifier / construct.Flag
            else:
                f_enum = enum.IntEnum(
                    identifier, [(op, 1 << i) for (i, op) in enumerate(options)]
                )
                s_field = identifier / construct.Enum(
                    construct.BitsInteger(bits), f_enum
                )

        struct_fields.append(s_field)
        if verbose:
            print(f"{identifier:15}: {description} ({len(options)} options)")
        assert bits == s_field.sizeof()
        total_bits += bits
    if verbose:
        print(f"Total bits: {total_bits}")
    return (struct_fields, total_bits)


class SubSpec:
    grammar = GRAMMAR
    struct_cls = None

    def __init__(self, **vars):
        self.vars = vars

    def to_bits(self):
        return self.struct_cls.build(self.vars)

    def to_code(self):
        return to_shortcode(self.to_bits())

    @classmethod
    def from_bits(cls, bits):
        st = cls.struct_cls.parse(bits)
        return cls(**dict(st))

    @classmethod
    def from_code(cls, code):
        return cls.from_bits(from_shortcode(code))

    def __repr__(self):
        return "<Sub %s (%s)>" % (self.to_code(), self.vars)


def subspec_from_grammar_file(filename, verbose=False, cls=SubSpec):
    with open(filename, "r") as infp:
        root = cls.grammar.parse(infp.read())
    fields = list(parse_grammar(root))
    struct_fields, total_bits = convert_fields_to_struct_fields(fields, verbose=verbose)
    req_padding = 8 - total_bits % 8
    if req_padding:
        fields.append("padding" / construct.Padding(req_padding))
    return type("SubSpec", (cls,), dict(struct_cls=construct.Struct(*struct_fields)))
