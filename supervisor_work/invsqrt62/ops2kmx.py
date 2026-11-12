"""Convert a circuit-viewer ops.json (manwithacat/kickmix-macos, Apache-2.0) to kickmix .kmx text.

Usage: python ops2kmx.py ops.json out.kmx
Op encoding: [kind, args..., cond] with cond = classical bit index or -1; Z_POW = [11, q, cond, float]
with the exact angle in zpow_exact[op index] as numerator / 2^128 TURNS (kickmix Z_POW takes half-turns).
"""
import json, sys
from decimal import Decimal, getcontext

getcontext().prec = 200


def exact_dec(num):
    v = Decimal(2 * int(num) % 2**129) / (Decimal(2) ** 128)  # turns -> kickmix half-turns
    s = format(v.normalize(), 'f')
    return s if '.' in s else s + '.0'


def main(src, dst):
    d = json.load(open(src))
    K = d['kinds']; Z = d.get('zpow_exact', {})
    out = [f'APPEND_TO_REGISTER q{q} r0' for q in d['x_qubits']] + ['REGISTER r0 "x"']
    c = lambda b: '' if b == -1 else f' if b{b}'
    for i, o in enumerate(d['ops']):
        k = K[o[0]]; a = o[1:]
        if k in ('X', 'Z', 'R'):
            out.append(f'{k} q{a[0]}{c(a[1])}')
        elif k in ('CX', 'CZ', 'SWAP'):
            out.append(f'{k} q{a[0]} q{a[1]}{c(a[2])}')
        elif k in ('CCX', 'CCZ', 'CSWAP'):
            out.append(f'{k} q{a[0]} q{a[1]} q{a[2]}{c(a[3])}')
        elif k == 'HMR':
            out.append(f'HMR q{a[0]} b{a[1]}{c(a[2])}')
        elif k == 'NEG':
            out.append(f'NEG{c(a[0])}')
        elif k == 'Z_POW':
            e = exact_dec(Z[str(i)]) if str(i) in Z else repr(a[2])
            assert abs(float(e) - (2 * a[2]) % 2) < 1e-12, (i, e, a)
            out.append(f'Z_POW q{a[0]} {e}{c(a[1])}')
        elif k in ('BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1'):
            out.append(f'{k} b{a[0]}{c(a[1])}')
        elif k == 'PUSH_CONDITION':
            out.append(f'PUSH_CONDITION if b{a[0]}')
        elif k == 'POP_CONDITION':
            out.append('POP_CONDITION')
        else:
            raise ValueError((i, o))
    open(dst, 'w').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
