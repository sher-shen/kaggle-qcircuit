"""LUT + piecewise polynomial invsqrt circuit (supervisor design, no Newton-Raphson).

1. Normalize x -> x_norm = x 4^s (official reference routine), M = x_norm / 2^20 in [1, 4).
2. QROM (kickmix init_lookup) on the top k bits of x_norm loads per-segment coefficients
   of a degree-`deg` polynomial in t = (low D bits of x_norm) / 2^D, D = 22 - k:
       f(M) = 1/sqrt(M) ~ a0 - t (b1 - t (b2 - t b3 ...))   (alternating signs, all b_j >= 0)
   evaluated by Horner in place with column-truncated multipliers (reference `_add_row`).
3. Denormalize by the unary flags (reference routine), phase per bit with Z_POW, uncompute.
Coefficients are fit per segment (Chebyshev nodes) and then the constant term is re-centred
using the exact integer model over every x_norm in [2^20, 2^22), so the worst error is measured,
not estimated.
"""
import os as _os, sys, math
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/data/kickmix'); sys.path.insert(0, ROOT + '/data/verifiers/invsqrt')
import numpy as np
from fractions import Fraction
import kickmix as km
from nr_reference_circuit import _normalize, _add_row, _denormalize
import flagpack

N_P, WIDTH = 10, 22
MAX_X = 3 * (2**N_P - 2)**2


class Design:
    def __init__(self, k=9, deg=2, fy=31, widths=None, guards=None, cadd=False, binshift=False, rangeq=False, packflags=False):
        self.cadd, self.binshift, self.rangeq, self.packflags = cadd, binshift, rangeq, packflags
        if packflags: self.binshift = True
        """widths[j]: bit width of register j (j=0 is y, Fy+1 bits); guards[j]: extra fractional
        bits of register j relative to y units (register j value ~ b_j 2^(fy+guards[j]))."""
        self.k, self.deg, self.fy = k, deg, fy
        self.D = WIDTH - k
        self.guards = guards or [0] + [2] * deg
        self.fit()
        self.widths = widths or self.auto_widths()

    # --- classical side -------------------------------------------------------------
    def fit(self):
        k, deg, D = self.k, self.deg, self.D
        nseg = 2**k
        coefs = np.zeros((nseg, deg + 1))
        h_m = 2.0**(D - 20)  # segment width in M units
        nodes = (1 - np.cos((2 * np.arange(deg + 1) + 1) * np.pi / (2 * (deg + 1)))) / 2  # in [0,1]
        for A in range(nseg // 4, nseg):
            m0 = A * h_m
            ts = nodes
            vals = 1 / np.sqrt(m0 + h_m * ts)
            p = np.polyfit(ts, vals, deg)[::-1]  # p[j] t^j
            coefs[A] = p
        self.real = coefs  # f ~ sum p_j t^j

    def int_coefs(self):
        fy, g = self.fy, self.guards
        out = []
        for j in range(self.deg + 1):
            mag = self.real[:, j] * (-1)**j  # a0, b1 = -p1, b2 = p2, ...
            out.append(np.round(mag * 2.0**(fy + g[j])).astype(np.int64))
        return out

    def auto_widths(self):
        ic = self.int_coefs()
        return [int(max(1, int(c.max()).bit_length())) + (1 if j == 0 else 0) for j, c in enumerate(ic)]

    def model(self, xn, coefs=None):
        """Integer pipeline replica for x_norm values xn. Returns y (units 2^-fy)."""
        D, deg, g = self.D, self.deg, self.guards
        coefs = coefs if coefs is not None else self.int_coefs()
        A = xn >> D
        t = xn & ((1 << D) - 1)
        regs = [c[A].copy() for c in coefs]
        for j in range(deg, 0, -1):  # regs[j-1] -= T(regs[j] * t), shifting by guard difference
            acc = np.zeros_like(xn)
            sh = g[j] - g[j - 1]  # regs[j] has sh more fractional bits than regs[j-1]
            for i in range(D):
                e = i - D - sh  # weight of row: t bit i -> 2^(i-D); convert units
                tb = (t >> i) & 1
                acc += tb * (regs[j] >> -e if e < 0 else regs[j] << e)
            regs[j - 1] = regs[j - 1] - acc
        return regs[0]

    def calibrate(self):
        """Re-centre a0 per segment using the exact model on all x_norm."""
        xn = np.arange(2**20, 2**22, dtype=np.int64)
        coefs = self.int_coefs()
        y = self.model(xn, coefs)
        exact = 2.0**self.fy / np.sqrt(xn / 2.0**20)
        err = y - exact
        A = xn >> self.D
        nseg = 2**self.k
        lo = np.full(nseg, np.inf); hi = np.full(nseg, -np.inf)
        np.minimum.at(lo, A, err); np.maximum.at(hi, A, err)
        shift = np.zeros(nseg, dtype=np.int64)
        ok = np.isfinite(lo)
        shift[ok] = np.round((lo[ok] + hi[ok]) / 2).astype(np.int64)
        coefs[0] = coefs[0] - shift
        self.coefs = coefs
        self.widths = [max(w, int(int(c.max()).bit_length()) + (1 if j == 0 else 0)) for j, (w, c) in enumerate(zip(self.widths, coefs))]
        return self.max_rel_err()

    def max_rel_err(self):
        xs = np.arange(1, MAX_X + 1, dtype=np.int64)
        s = (WIDTH - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
        xn = xs << (2 * s)
        y = self.model(xn, self.coefs)
        approx = y.astype(np.float64) * 2.0**(s - N_P) / 2.0**self.fy
        rel = np.abs(approx * np.sqrt(xs) - 1)
        # wrap: x=1 gives y=2^fy exactly representable (fy+1 bits)
        return rel.max()

    # --- circuit ----------------------------------------------------------------------
    def build(self):
        k, D, deg, fy, g = self.k, self.D, self.deg, self.fy, self.guards
        b = km.CircuitBuilder()
        x = b.create_quantum_register(WIDTH, name='x')
        flags = b.alloc_qubits(N_P)
        with b.mark('normalize'):
            _normalize(b, False, x, flags)
        sbp = None
        if self.packflags:
            sbp = b.alloc_qubits(4); flagpack.pack(b, flags, sbp); b.free(flags)
        regs = [b.alloc_qubits(w) for w in self.widths]
        sw = max(self.widths)
        scratch = None if self.cadd else b.alloc_qubits(sw)
        out_len = self.widths[0] + N_P
        table = [0] * 2**k
        off = 0
        for j, c in enumerate(self.coefs):
            for A in range(2**k):
                v = int(c[A])
                assert 0 <= v < 2**self.widths[j], (j, A, v)
                table[A] |= v << off
            off += self.widths[j]
        target = km.array([q for r in regs for q in r])
        address = x[D:]
        tbits = [x[i] for i in range(D)]

        def horner(inverse):
            order = range(deg, 0, -1)
            for j in (reversed(order) if inverse else order):
                sh = g[j] - g[j - 1]
                src, acc = regs[j], regs[j - 1]
                for i in range(D):
                    e = i - D - sh  # src bit q (weight 2^q) lands at acc index q + e
                    terms = [(src[q], q + e) for q in range(len(src)) if 0 <= q + e < len(acc)]
                    if not terms:
                        continue
                    if self.cadd:
                        q0 = terms[0][0]; lo = terms[0][1]
                        qs = [q for q, _ in terms]
                        src_slice = km.array(qs)
                        if inverse:
                            b.iadd(src_slice, target=acc[lo:], control=tbits[i])
                        else:
                            b.isub(src_slice, target=acc[lo:], control=tbits[i])
                    else:
                        _add_row(b, inverse, tbits[i], terms, acc, scratch, subtract=True)

        with b.mark('lookup'):
            if self.rangeq:  # visit only reachable addresses (top pair of x_norm is nonzero)
                with b.unary_iteration(address, range(2**(k - 2), 2**k)) as it:
                    for v, mq in it:
                        b.gf2_iadd(table[v], target=target, control=mq)
            else:
                b.init_lookup(table=table, address=address, target=target)
        with b.mark('horner'):
            horner(False)
        # free the higher Horner registers early: they are restored only by uncomputing, so keep.
        y1 = km.array(list(regs[0]) + list(b.alloc_qubits(N_P)))
        SB = {0: range(10), 1: (1, 3, 5, 7, 9), 2: (3, 7), 3: (7,)}  # binary s from thermometer flags (Clifford)
        def sbits_load(sb):
            for r, idx in SB.items():
                for i in idx:
                    b.cx(flags[i], sb[r])
        def denorm(inverse):
            if not self.binshift:
                _denormalize(b, inverse, flags, y1); return
            if sbp is not None:
                sb = sbp
            else:
                sb = b.alloc_qubits(4); sbits_load(sb)
            L = len(y1)
            for r in ((0, 1, 2, 3) if inverse else (3, 2, 1, 0)):
                if self.packflags:  # trimmed lane: value bits (incl. the 2^fy bit) + max shift reachable with bit r set (s <= 10)
                    L = self.widths[0] + max(v & ~((1 << r) - 1) for v in range(11) if v >> r & 1)
                if inverse:
                    b.right_rotate(y1[:L], 2**r, control=sb[r])
                else:
                    b.left_rotate(y1[:L], 2**r, control=sb[r])
            if sbp is None:
                sbits_load(sb); b.free(sb)
        with b.mark('denormalize'):
            denorm(False)
        F = fy + N_P  # y1 / 2^F = 1/sqrt(x)
        with b.mark('phase'):
            for j in range(len(y1)):
                if j < F:
                    b.z_pow(y1[j], Fraction(2)**(j - F + 1))
        with b.mark('denormalize_inv'):
            denorm(True)
        b.free(y1[self.widths[0]:])
        with b.mark('horner_inv'):
            horner(True)
        with b.mark('lookup_inv'):
            b.del_lookup(table=table, address=address, target=target)
        for r in regs + ([] if scratch is None else [scratch]):
            b.free(r)
        if sbp is not None:
            flags = b.alloc_qubits(N_P); flagpack.unpack(b, flags, sbp); b.free(sbp)
        with b.mark('normalize_inv'):
            _normalize(b, True, x, flags)
        b.free(flags)
        return b.finish_circuit()


if __name__ == '__main__':
    import argparse, hashlib
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=9); ap.add_argument('--deg', type=int, default=2)
    ap.add_argument('--fy', type=int, default=31); ap.add_argument('--guards', default=None)
    ap.add_argument('--out', default=None); ap.add_argument('--cadd', action='store_true')
    ap.add_argument('--binshift', action='store_true'); ap.add_argument('--rangeq', action='store_true')
    ap.add_argument('--packflags', action='store_true')
    a = ap.parse_args()
    d = Design(a.k, a.deg, a.fy, guards=[int(v) for v in a.guards.split(',')] if a.guards else None, cadd=a.cadd, binshift=a.binshift, rangeq=a.rangeq, packflags=a.packflags)
    e = d.calibrate()
    print(f'k={a.k} deg={a.deg} fy={a.fy} guards={d.guards} widths={d.widths} max rel err 2^{math.log2(e):.2f}')
    c = d.build()
    print('qubits', c.num_qubits, 'toffoli(static)', c.operation_statistics().num_toffoli_like)
    if a.out:
        c.to_file(a.out, format='kmb')
        print(a.out, hashlib.sha256(open(a.out, 'rb').read()).hexdigest()[:16])
