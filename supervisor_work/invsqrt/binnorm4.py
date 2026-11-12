"""binnorm2 forward + per-stage measurement-based erasure of s in the inverse (supervisor, 2026-11-08).

Inverse: un-shift stage r (r = 0, 1, 2, 3, i.e. by 2, 4, 8, 16), then immediately X-measure s_r (HMR -> m_r).
After un-shifting stages 0..r the register holds x_norm >> (2 s0 + ... + 2^(r+1) s_r), whose leading-zero
count is z_norm + sum_{q<=r} 2^(q+1) s_q with z_norm in {0, 1} (x_norm >= 2^20), so
s_r = P_{2^(r+1)}(current x) = [top 2^(r+1) bits zero].  The leftover phase (-1)^(m_r s_r) is a
multi-controlled Z on the 2^(r+1) negated top bits, run only when m_r = 1: n - 2 ANDs (measurement-
uncomputed) + one CZ.  Expected Toffoli count with uniform m: (0 + 2 + 6 + 14) / 2 = 11 (binnorm3: 15.125).
"""
import binnorm as _b
from binnorm2 import _chain_xor


def _phase_P(b, x, n, cond):
    bits = [x[len(x) - 1 - i] for i in range(n)]
    b.push_condition(cond)
    b.x(bits)
    if n == 2:
        b.cz(bits[0], bits[1])
    else:
        p = b.alloc_qubits(n - 2)
        b.init_and(bits[0], bits[1], p[0])
        for i in range(1, n - 2):
            b.init_and(p[i - 1], bits[i + 1], p[i])
        b.cz(p[n - 3], bits[n - 1])
        for i in range(n - 3, 0, -1):
            b.del_and(p[i - 1], bits[i + 1], p[i])
        b.del_and(bits[0], bits[1], p[0])
        b.free(p)
    b.x(bits)
    b.pop_condition()


def normalize(b, x, sb, inverse=False):
    if not inverse:
        _chain_xor(b, x, sb)
        for r in (3, 2, 1, 0):
            _b._shift(b, x, 2 ** (r + 1), sb[r], False)
    else:
        m = b.alloc_bits(4)
        for r in (0, 1, 2, 3):
            _b._shift(b, x, 2 ** (r + 1), sb[r], True)
            b.hmr([sb[r]], [m[r]])
            _phase_P(b, x, 2 ** (r + 1), m[r])
