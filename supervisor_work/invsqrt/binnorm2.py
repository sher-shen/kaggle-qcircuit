"""Binary-search normalization with ONE prefix AND chain (supervisor, 2026-11-07).

P_{2k} = [top 2k bits of x are zero] = [s >= k], k = 1..10, are the even prefixes of a single
AND chain over the negated bits x[21], x[20], ..., x[2] (19 ANDs). The bits of s are XORs of them:
  s0 = P2 ^ P4 ^ ... ^ P20,  s1 = P4 ^ P8 ^ P12 ^ P16 ^ P20,  s2 = P8 ^ P16,  s3 = P16
(bit r of s toggles at every multiple of 2^r).  So s is computed from the ORIGINAL x with CX
gates, the chain is erased by measurement (del_and, no Toffoli), then the four zero-top shifts
follow (same CSWAPs as binnorm.py).  Inverse: un-shift, recompute the chain, clear s with the
same CXs, erase the chain.  19 + 19 Toffoli instead of 26 + 22 in binnorm.py.
"""
import binnorm as _b

TAPS = {0: (2, 4, 6, 8, 10, 12, 14, 16, 18, 20), 1: (4, 8, 12, 16, 20), 2: (8, 16), 3: (16,)}


def _chain_xor(b, x, sb):
    bits = [x[len(x) - 1 - i] for i in range(20)]  # x21, x20, ..., x2
    b.x(bits)
    p = b.alloc_qubits(19)  # p[i] = AND of bits[0..i+1]; P_{n} = p[n-2]
    b.init_and(bits[0], bits[1], p[0])
    for i in range(1, 19):
        b.init_and(p[i - 1], bits[i + 1], p[i])
    for r, ns in TAPS.items():
        for n in ns:
            b.cx(p[n - 2], sb[r])
    for i in range(18, 0, -1):
        b.del_and(p[i - 1], bits[i + 1], p[i])
    b.del_and(bits[0], bits[1], p[0])
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
        _chain_xor(b, x, sb)
