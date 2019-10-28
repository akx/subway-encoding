import math
import itertools
import construct

values = {}
for value, chs in enumerate(itertools.product("bcdfghjklmnprstvwxz", "aeiou")):
    values[value] = "".join(chs)

inv_values = {chs: value for (value, chs) in values.items()}
value_bits = int(math.log2(max(values)))  # not ceil!
value_bint = construct.BitsInteger(value_bits)
value_enc_len = max(len(chs) for chs in inv_values)


def to_shortcode(bits: bytes) -> str:
    acc = []
    for start in range(0, len(bits), value_bits):
        slice = bits[start : start + value_bits].ljust(value_bits, b"\x00")
        chs = values[value_bint.parse(slice)]
        if acc and chs == acc[-1][0]:
            acc[-1][1] += 1
        else:
            acc.append([chs, 1, value])

    return "".join((s * n if n == 1 or n > 9 else f"{n}{s}") for (s, n, v) in acc)


def from_shortcode(shortcode: str) -> bytes:
    bits = []
    i = 0
    n = 1
    while i < len(shortcode):
        if shortcode[i].isdigit():
            n = int(shortcode[i])
            i += 1
        else:
            chs = shortcode[i : i + value_enc_len]
            value = inv_values[chs]
            bits.append(value_bint.build(value) * n)
            i += value_enc_len
            n = 1
    return b"".join(bits)
