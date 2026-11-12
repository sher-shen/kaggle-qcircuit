"""binnorm2 + measurement-based erasure of s in the inverse (supervisor, 2026-11-07 23:xx UTC).

Inverse: un-shift x, then X-measure the four s qubits (HMR -> m) instead of recomputing the chain.
The leftover phase is (-1)^(m.s(x)) = prod_n (-1)^(c_n P_n) with c_n = XOR of m_r over the r whose
tap list contains n (s_r = XOR of P_n).  It is undone with a prefix AND chain over the negated top
bits that only runs as far as the largest n with c_n = 1 (classically conditioned AND steps), a
CZ for every P_n with c_n = 1, and measurement-based uncomputation.  Expected Toffoli count with
uniformly random m: 15.125 instead of 19.
"""
import binnorm as _b
from binnorm2 import TAPS, _chain_xor

NS = list(range(2, 21, 2))


def _erase_s(b, x, sb):
    m = b.alloc_bits(4)
    b.hmr(list(sb), list(m))
    c = {}
    for n in NS:
        c[n] = b.alloc_bits(1)[0]
        b.bit_store(c[n], False)
        for r, ns in TAPS.items():
            if n in ns:
                b.cx(m[r], c[n])
    need = []
    for i in range(18):  # p[i] needed iff some c_n = 1 with n - 3 >= i
        nb = b.alloc_bits(1)[0]
        b.bit_store(nb, False)
        for n in NS:
            if n - 3 >= i:
                b.bit_store(nb, True, control=c[n])
        need.append(nb)
    bits = [x[len(x) - 1 - i] for i in range(20)]
    b.x(bits)
    p = b.alloc_qubits(18)
    for i in range(18):
        b.push_condition(need[i])
        b.init_and(bits[0] if i == 0 else p[i - 1], bits[i + 1], p[i])
        b.pop_condition()
    for n in NS:
        b.push_condition(c[n])
        b.cz(bits[0] if n == 2 else p[n - 3], bits[n - 1])
        b.pop_condition()
    for i in range(17, -1, -1):
        b.push_condition(need[i])
        b.del_and(bits[0] if i == 0 else p[i - 1], bits[i + 1], p[i])
        b.pop_condition()
    b.free(p)
    b.x(bits)


def normalize(b, x, sb, inverse=False):
    if not inverse:
        _chain_xor(b, x, sb)
        for r in (3, 2, 1, 0):
            _b._shift(b, x, 2 ** (r + 1), sb[r], False)
    else:
        for r in (0, 1, 2, 3):
            _b._shift(b, x, 2 ** (r + 1), sb[r], True)
        _erase_s(b, x, sb)
