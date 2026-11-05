"""LUT + quadratic invsqrt, v2: nonuniform segments (supervisor design).

Same pipeline as lutpoly.py (normalize -> QROM coefficients -> Horner -> binary-shift denormalize ->
Z_POW per bit -> uncompute), but:
  * t = low D bits of x_norm for every segment (D = 22 - k_lo - ... see seg()), and segments are
    2^-(klo-2) wide on M in [1,2) and twice as wide on M in [2,4) (f''' is 2^-3.5 smaller there);
  * the QROM is two unary-iteration passes that only visit reachable addresses
    (M in [1,2): bits 13..20 under !bit21; M in [2,4): bits 14..21), ~2^(klo-1) Toffolis in total
    instead of 2^klo for init_lookup;
  * deletion uses kickmix del_lookup on the expanded 2^klo table (measurement based).
"""
import os as _os, sys, math
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/data/kickmix'); sys.path.insert(0, ROOT + '/data/verifiers/invsqrt')
import numpy as np
from fractions import Fraction
import kickmix as km
from nr_reference_circuit import _normalize, _add_row

N_P, WIDTH = 10, 22
MAX_X = 3 * (2**N_P - 2)**2
SB = {0: range(10), 1: (1, 3, 5, 7, 9), 2: (3, 7), 3: (7,)}  # binary s from thermometer flags


class Design:
    def __init__(self, klo=9, deg=2, fy=28, guards=None, sub_fit=True):
        self.klo, self.deg, self.fy = klo, deg, fy
        self.lo_shift = WIDTH - klo          # address bits for M<2 start here (13 for klo=9)
        self.D = self.lo_shift + 1           # t bits (14): one more than the M<2 segment width
        self.guards = guards or [0] + [1] * deg
        self.nlo = 2**(klo - 2)              # segments on [1,2): addresses 2^(klo-2) .. 2^(klo-1)-1
        self.fit()

    def seg_of(self, xn):
        hi = xn >> (WIDTH - 1)
        a_lo = (xn >> self.lo_shift) - self.nlo                     # 0..nlo-1 when hi == 0
        a_hi = (xn >> self.D) - (2**(WIDTH - 1 - self.D)) + self.nlo  # nlo..2nlo-1 when hi == 1
        return np.where(hi == 1, a_hi, a_lo)

    def fit(self):
        deg, D = self.deg, self.D
        nseg = 2 * self.nlo
        self.real = np.zeros((nseg, deg + 1))
        nodes = (1 - np.cos((2 * np.arange(deg + 1) + 1) * np.pi / (2 * (deg + 1)))) / 2
        for sgi in range(nseg):
            if sgi < self.nlo:   # x_norm range [base, base + 2^lo_shift), t starts at t0
                base = (sgi + self.nlo) << self.lo_shift; span = 1 << self.lo_shift
            else:
                base = (sgi - self.nlo + 2**(WIDTH - 1 - D)) << D; span = 1 << D
            t0 = (base & ((1 << D) - 1)) / 2**D
            ts = t0 + nodes * span / 2**D
            vals = 1 / np.sqrt((base - (base & ((1 << D) - 1)) + ts * 2**D) / 2.0**20)
            self.real[sgi] = np.polyfit(ts, vals, deg)[::-1]

    def int_coefs(self):
        return [np.round(self.real[:, j] * (-1)**j * 2.0**(self.fy + self.guards[j])).astype(np.int64)
                for j in range(self.deg + 1)]

    def model(self, xn, coefs):
        D, deg, g = self.D, self.deg, self.guards
        sg = self.seg_of(xn); t = xn & ((1 << D) - 1)
        regs = [c[sg].copy() for c in coefs]
        for j in range(deg, 0, -1):
            acc = np.zeros_like(xn); sh = g[j] - g[j - 1]
            w = self.widths[j - 1] if hasattr(self, 'widths') else 64
            for i in range(D):
                e = i - D - sh
                acc += ((t >> i) & 1) * (regs[j] >> -e if e < 0 else regs[j] << e)
            regs[j - 1] = regs[j - 1] - acc
            if (regs[j - 1] < 0).any():
                raise OverflowError('negative Horner intermediate')
        return regs[0]

    def calibrate(self):
        xn = np.arange(2**20, 2**22, dtype=np.int64)
        coefs = self.int_coefs()
        y = self.model(xn, coefs)
        err = y - 2.0**self.fy / np.sqrt(xn / 2.0**20)
        sg = self.seg_of(xn); nseg = 2 * self.nlo
        lo = np.full(nseg, np.inf); hi = np.full(nseg, -np.inf)
        np.minimum.at(lo, sg, err); np.maximum.at(hi, sg, err)
        coefs[0] = coefs[0] - np.round((lo + hi) / 2).astype(np.int64)
        self.coefs = coefs
        self.widths = [int(int(c.max()).bit_length()) for c in coefs]
        self.widths[0] = max(self.widths[0], self.fy + 1)
        xs = np.arange(1, MAX_X + 1, dtype=np.int64)
        s = (WIDTH - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
        y = self.model(xs << (2 * s), coefs)
        if (y >= 2**self.widths[0]).any():
            raise OverflowError('y overflow')
        rel = np.abs(y * 2.0**(s - N_P) / 2.0**self.fy * np.sqrt(xs) - 1)
        return rel.max()

    def packed(self, sgi):
        v, off = 0, 0
        for j, c in enumerate(self.coefs):
            val = int(c[sgi]); assert 0 <= val < 2**self.widths[j]; v |= val << off; off += self.widths[j]
        return v

    def build(self):
        D, deg, fy, g = self.D, self.deg, self.fy, self.guards
        b = km.CircuitBuilder()
        x = b.create_quantum_register(WIDTH, name='x')
        flags = b.alloc_qubits(N_P)
        regs = [b.alloc_qubits(w) for w in self.widths]
        scratch = b.alloc_qubits(max(self.widths))
        target = km.array([q for r in regs for q in r])
        tbits = [x[i] for i in range(D)]
        top = x[WIDTH - 1]
        # expanded 2^klo table on address bits lo_shift..21 for del_lookup
        full = [0] * 2**self.klo
        for a in range(2**self.klo):
            if a >= self.nlo:
                xn = a << self.lo_shift
                full[a] = self.packed(int(self.seg_of(np.array([xn]))[0]))

        def qrom():
            b.x(top)
            with b.unary_iteration(x[self.lo_shift:WIDTH - 1], range(self.nlo, 2 * self.nlo), control=top) as it:
                for v, mq in it:
                    b.gf2_iadd(self.packed(v - self.nlo), target=target, control=mq)
            b.x(top)
            nhi = 2**(WIDTH - 1 - D)
            with b.unary_iteration(x[D:], range(nhi, 2 * nhi)) as it:
                for v, mq in it:
                    b.gf2_iadd(self.packed(v - nhi + self.nlo), target=target, control=mq)

        def horner(inverse):
            order = range(deg, 0, -1)
            for j in (reversed(order) if inverse else order):
                sh = g[j] - g[j - 1]; src, acc = regs[j], regs[j - 1]
                for i in range(D):
                    e = i - D - sh
                    terms = [(src[q], q + e) for q in range(len(src)) if 0 <= q + e < len(acc)]
                    if terms:
                        _add_row(b, inverse, tbits[i], terms, acc, scratch, subtract=True)

        y1 = None
        def denorm(inverse):
            sb = b.alloc_qubits(4)
            for r, idx in SB.items():
                for i in idx: b.cx(flags[i], sb[r])
            for r in ((0, 1, 2, 3) if inverse else (3, 2, 1, 0)):
                (b.right_rotate if inverse else b.left_rotate)(y1, 2**r, control=sb[r])
            for r, idx in SB.items():
                for i in idx: b.cx(flags[i], sb[r])
            b.free(sb)

        with b.mark('normalize'): _normalize(b, False, x, flags)
        with b.mark('lookup'): qrom()
        with b.mark('horner'): horner(False)
        y1 = km.array(list(regs[0]) + list(b.alloc_qubits(N_P)))
        with b.mark('denormalize'): denorm(False)
        F = fy + N_P
        with b.mark('phase'):
            for j in range(len(y1)):
                if j < F:
                    b.z_pow(y1[j], Fraction(2)**(j - F + 1))
        with b.mark('denormalize_inv'): denorm(True)
        b.free(y1[self.widths[0]:])
        with b.mark('horner_inv'): horner(True)
        with b.mark('lookup_inv'):
            b.del_lookup(table=full, address=x[self.lo_shift:], target=target)
        with b.mark('normalize_inv'): _normalize(b, True, x, flags)
        for r in regs + [scratch, flags]:
            b.free(r)
        return b.finish_circuit()


if __name__ == '__main__':
    import argparse, hashlib
    ap = argparse.ArgumentParser()
    ap.add_argument('--klo', type=int, default=9); ap.add_argument('--deg', type=int, default=2)
    ap.add_argument('--fy', type=int, default=28); ap.add_argument('--guards', default=None)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    d = Design(a.klo, a.deg, a.fy, guards=[int(v) for v in a.guards.split(',')] if a.guards else None)
    e = d.calibrate()
    print(f'klo={a.klo} deg={a.deg} fy={a.fy} guards={d.guards} widths={d.widths} max rel err 2^{math.log2(e):.2f}')
    c = d.build()
    print('qubits', c.num_qubits, 'toffoli(static)', c.operation_statistics().num_toffoli_like)
    if a.out:
        c.to_file(a.out, format='kmb')
        print(a.out, hashlib.sha256(open(a.out, 'rb').read()).hexdigest()[:16])
