"""lutpoly14 = lutpoly11 + --groups j:a:LA (Horner step j: rows i<a go into a narrow window of LA bits plus
its own 2 signed carry qubits, folded into the main window once; all adders use the top-CCX Gidney adder of
lutpoly13 when --topccx is given).
lutpoly11 = lutpoly6 + --gadd: own Gidney adder (init_and/del_and) with implicit zero source
extension and native carry-in, so the zero pad register and the rounding bit l are not needed.
lutpoly6 = lutpoly4 + --droprot (skip the Z_POW on the lowest m bits of the output lane).
Windowed signed-digit variant (lutpoly4): Horner rows add only into the low L_j bits of the
accumulator plus 2 signed carry qubits; carries are folded into the high part once per step.
Signed-digit variant (lutpoly3): delta digits +-1 so every Horner row is a CX-conjugated plain add.
LUT + piecewise polynomial invsqrt circuit (supervisor design, no Newton-Raphson).

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
import flagpack, binnorm
if '--topccx' in sys.argv:
    sys.argv.remove('--topccx')
    import lutpoly13 as _l13
    gadd = None  # replaced below after definition
    _TOP = True
else:
    _TOP = False

N_P, WIDTH = 10, 22
MAX_X = 3 * (2**N_P - 2)**2


def gadd(b, src, tgt, cin=None, sub=False):
    """tgt += src (+cin) mod 2^n (sub: tgt -= src + cin). src may be shorter than tgt (implicit zeros)."""
    src, tgt = list(src), list(tgt); n, m = len(tgt), len(src)
    assert m <= n
    if n == 0 or (m == 0 and cin is None): return
    if sub: b.x(km.array(tgt))
    c = [None] + (list(b.alloc_qubits(n - 1)) if n > 1 else [])
    def cq(i): return cin if i == 0 else c[i]
    for i in range(n - 1):
        ci, ai, bi = cq(i), (src[i] if i < m else None), tgt[i]
        if ci is None: b.init_and(ai, bi, c[1])
        elif ai is None: b.init_and(bi, ci, c[i + 1])
        else:
            b.cx(ci, ai); b.cx(ci, bi); b.init_and(ai, bi, c[i + 1]); b.cx(ci, c[i + 1])
    if n - 1 < m: b.cx(src[n - 1], tgt[n - 1])
    if cq(n - 1) is not None: b.cx(cq(n - 1), tgt[n - 1])
    for i in range(n - 2, -1, -1):
        ci, ai, bi = cq(i), (src[i] if i < m else None), tgt[i]
        if ci is None: b.del_and(ai, bi, c[1]); b.cx(ai, bi)
        elif ai is None: b.del_and(bi, ci, c[i + 1]); b.cx(ci, bi)
        else:
            b.cx(ci, c[i + 1]); b.del_and(ai, bi, c[i + 1]); b.cx(ci, ai); b.cx(ai, bi)
    if n > 1: b.free(km.array(c[1:]))
    if sub: b.x(km.array(tgt))


if _TOP: gadd = _l13.gadd_top


class Design:
    def __init__(self, k=9, deg=2, fy=31, widths=None, guards=None, cadd=False, binshift=False, rangeq=False, packflags=False):
        self.cadd, self.binshift, self.rangeq, self.packflags = cadd, binshift, rangeq, packflags
        if packflags: self.binshift = True
        """widths[j]: bit width of register j (j=0 is y, Fy+1 bits); guards[j]: extra fractional
        bits of register j relative to y units (register j value ~ b_j 2^(fy+guards[j]))."""
        self.k, self.deg, self.fy = k, deg, fy
        self.D = WIDTH - k
        self.guards = guards or [0] + [2] * deg
        self.extra = [0] * (deg + 1)
        self.pad = 0
        self.fit()
        self.widths = widths or self.auto_widths()

    # --- classical side -------------------------------------------------------------
    def fit(self):
        k, deg, D = self.k, self.deg, self.D
        nseg = 2**k
        coefs = np.zeros((nseg, deg + 1))
        h_m = 2.0**(D - 20)  # segment width in M units
        nodes = -np.cos((2 * np.arange(deg + 1) + 1) * np.pi / (2 * (deg + 1)))  # in (-1,1)
        for A in range(nseg // 4, nseg):
            m0 = A * h_m
            ts = nodes  # delta = (2t+1-2^D)/2^D, M = m0 + h/2 + h delta/2
            vals = 1 / np.sqrt(m0 + h_m / 2 + h_m * ts / 2)
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
        return [int(max(1, int(c.max()).bit_length())) + (1 if j == 0 else 0) + self.extra[j] for j, c in enumerate(ic)]

    def _old_auto_widths(self):
        ic = self.int_coefs()
        return [int(max(1, int(c.max()).bit_length())) + (1 if j == 0 else 0) for j, c in enumerate(ic)]

    def model(self, xn, coefs=None):
        """Integer pipeline replica for x_norm values xn. Returns y (units 2^-fy)."""
        D, deg, g = self.D, self.deg, self.guards
        coefs = coefs if coefs is not None else self.int_coefs()
        A = xn >> D
        t = xn & ((1 << D) - 1)
        regs = [c[A].copy() for c in coefs]
        self._steps = {}
        for j in range(deg, 0, -1):
            init = regs[j - 1].copy()  # regs[j-1] -= T(regs[j] * t), shifting by guard difference
            acc = np.zeros_like(xn)
            sh = g[j] - g[j - 1]  # regs[j] has sh more fractional bits than regs[j-1]
            for i in range(D):
                e = i - D - sh  # weight of row: t bit i -> 2^(i-D); convert units
                sg = 2 * ((t >> i) & 1) - 1  # signed digit +-1
                v = regs[j] >> -e if e < 0 else regs[j] << e
                if e < 0 and j in getattr(self, 'round', ()):  # --round: carry-in = next-lower src bit (round to nearest)
                    v = v + ((regs[j] >> (-e - 1)) & 1)
                acc += sg * v
            regs[j - 1] = regs[j - 1] - acc
            self._steps[j] = (init, regs[j - 1])
            W = self.widths[j - 1] if hasattr(self, 'widths') else 64
            if hasattr(self, 'widths') and ((regs[j - 1] < 0) | (regs[j - 1] >= 2**W)).any():
                raise OverflowError(f'reg {j-1} out of range [{regs[j-1].min()},{regs[j-1].max()}] W={W}')
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
        if getattr(self, 'clamp', False):  # keep y < 2^fy so y needs fy bits (only M ~ 1 touches 2^fy)
            for _ in range(8):
                y = self.model(xn, coefs)
                over = np.zeros(nseg, dtype=np.int64)
                np.maximum.at(over, A, y - (2**self.fy - 1))
                if over.max() <= 0: break
                coefs[0] = coefs[0] - over
            self.widths = [w - (1 if j == 0 else 0) for j, w in enumerate(self.widths)]
            self.coefs = coefs
            return self.max_rel_err()
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

    def choose_L(self):
        xn = np.arange(2**20, 2**22, dtype=np.int64)
        self.model(xn, self.coefs)
        self.L = {}
        for j, (init, fin) in self._steps.items():
            for L in range(1, 64):
                low = (init & ((1 << L) - 1)) - (init - fin)
                if low.min() >= -2**(L + 1) and low.max() < 2**(L + 1):
                    break
            self.L[j] = min(L, self.widths[j - 1] - 2)
        return self.L

    # --- circuit ----------------------------------------------------------------------
    def build(self):
        k, D, deg, fy, g = self.k, self.D, self.deg, self.fy, self.guards
        b = km.CircuitBuilder()
        if getattr(self, 'maxq', None): b.set_max_qubits(self.maxq)
        x = b.create_quantum_register(WIDTH, name='x')
        sbp = None
        if getattr(self, 'binnorm', False):
            sbp = b.alloc_qubits(4)
            with b.mark('normalize'):
                binnorm.normalize(b, x, sbp, False)
        else:
            flags = b.alloc_qubits(N_P)
            with b.mark('normalize'):
                _normalize(b, False, x, flags)
        if self.packflags and sbp is None:
            sbp = b.alloc_qubits(4); flagpack.pack(b, flags, sbp); b.free(flags)
        dt = 1 if getattr(self, 'droptop', False) else 0  # y's top bit is always 1 (y in [2^(fy-1), 2^fy)): not stored during Horner
        regs = [b.alloc_qubits(w - (dt if j == 0 else 0)) for j, w in enumerate(self.widths)]
        scratch = None
        pad = b.alloc_qubits(self.pad) if self.pad else []
        carry = {j: b.alloc_qubits(2) for j in range(1, deg + 1)}
        out_len = self.widths[0] + N_P
        table = [0] * 2**k
        off = 0
        for j, c in enumerate(self.coefs):
            for A in range(2**k):
                v = int(c[A])
                if j == 0 and dt:
                    v = (v - 2**(self.widths[0] - 1)) % 2**(self.widths[0] - 1)
                assert 0 <= v < 2**len(regs[j]), (j, A, v)
                table[A] |= v << off
            off += len(regs[j])
        target = km.array([q for r in regs for q in r])
        address = x[D:]
        tbits = [x[i] for i in range(D)]

        def horner(inverse):
            order = range(deg, 0, -1)
            for j in (reversed(order) if inverse else order):
                sh = g[j] - g[j - 1]
                src, accfull = regs[j], regs[j - 1]
                L = self.L[j]
                acc = km.array(list(accfull[:L]) + list(carry[j]))
                hi = accfull[L:]
                def fold(inv):  # --foldadd: hi += c0 - 2 c1 as one adder, source bits [c0, c1, c1, ...] (fan-out copies of c1)
                    fan = b.alloc_qubits(len(hi) - 1)
                    for q in fan: b.cx(carry[j][1], q)
                    if G: gadd(b, [carry[j][0]] + list(fan), hi, sub=inv)
                    else: (b.isub if inv else b.iadd)(km.array([carry[j][0]] + list(fan)), target=hi)
                    for q in fan: b.cx(carry[j][1], q)
                    b.free(fan)
                foldadd = getattr(self, 'foldadd', False)
                G = getattr(self, 'gadd', False)
                if inverse and foldadd:
                    fold(True)
                elif inverse:
                    b.iadd(1, target=accfull[L + 1:], control=carry[j][1])
                    b.isub(1, target=hi, control=carry[j][0])
                def row(i, acc):
                    e = i - D - sh  # src bit q (weight 2^q) lands at acc index q + e
                    terms = [(src[q], q + e) for q in range(len(src)) if 0 <= q + e < len(acc)]
                    if not terms:
                        return
                    lo = terms[0][1]
                    assert all(p == lo + n for n, (_, p) in enumerate(terms))
                    tgt = acc[lo:]
                    srcq = [q for q, _ in terms]
                    npad = max(0, len(tgt) - len(srcq))
                    srcq += list(pad[:npad])
                    src_slice = km.array(srcq)
                    rnd = e < 0 and j in getattr(self, 'round', ())
                    if G:
                        cb = src[-e - 1] if rnd else None
                        for q in tgt: b.cx(tbits[i], q)
                        gadd(b, srcq, list(tgt), cin=cb, sub=inverse)
                        for q in tgt: b.cx(tbits[i], q)
                        return
                    if rnd:  # carry-in cb via an extra low bit l = cb: [l, tgt] += [cb, src] leaves l = 0
                        cb = src[-e - 1]
                        own = npad >= len(pad)
                        l = b.alloc_qubits(1)[0] if own else pad[npad]
                        tgt_r = km.array([l] + list(tgt)); src_r = km.array([cb] + srcq)
                    # acc -= (2d-1) v  ==  d ? ~(~acc + v) : acc + v   (inverse: isub)
                    for q in tgt: b.cx(tbits[i], q)
                    if rnd and not inverse:
                        b.cx(cb, l); b.iadd(src_r, target=tgt_r)
                    elif rnd:
                        b.isub(src_r, target=tgt_r); b.cx(cb, l)
                    else:
                        (b.isub if inverse else b.iadd)(src_slice, target=tgt)
                    for q in tgt: b.cx(tbits[i], q)
                    if rnd and own:
                        b.free(km.array([l]))

                grp = getattr(self, 'groups', {}).get(j)
                A_rows = list(range(grp[0])) if grp else []
                B_rows = [i for i in range(D) if i not in A_rows]
                def foldA(inv):  # window B bits [L_A, L) + carry pair += cA0 - 2 cA1
                    LA = grp[1]; cA = self._cA[j]
                    tg = list(accfull[LA:L]) + list(carry[j])
                    fan = b.alloc_qubits(len(tg) - 1)
                    for q in fan: b.cx(cA[1], q)
                    gadd(b, [cA[0]] + list(fan), tg, sub=inv)
                    for q in fan: b.cx(cA[1], q)
                    b.free(fan)
                if grp and not inverse:
                    self._cA = getattr(self, '_cA', {}); self._cA[j] = b.alloc_qubits(2)
                    accA = km.array(list(accfull[:grp[1]]) + list(self._cA[j]))
                    for i in A_rows: row(i, accA)
                    foldA(False)
                for i in B_rows: row(i, acc)
                if grp and inverse:
                    foldA(True)
                    accA = km.array(list(accfull[:grp[1]]) + list(self._cA[j]))
                    for i in A_rows: row(i, accA)
                    b.free(self._cA[j])
                if not inverse and foldadd:
                    fold(False)
                elif not inverse:
                    b.iadd(1, target=hi, control=carry[j][0])
                    b.isub(1, target=accfull[L + 1:], control=carry[j][1])

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
        topq = []
        if dt:
            topq = list(b.alloc_qubits(1)); b.x(topq[0])
        y1 = km.array(list(regs[0]) + topq + list(b.alloc_qubits(N_P)))
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
            if getattr(self, 'smallfirst', False):  # shift by 1,2,4,8 in that order: lanes stay short (122 vs 132 CSWAPs)
                fwd = (0, 1, 2, 3)
                for i, r in enumerate(reversed(fwd) if inverse else fwd):
                    m = 2**r
                    prev = sum(2**q for q in fwd[:fwd.index(r)])
                    nb = self.widths[0] + max(v & prev for v in range(11) if v >> r & 1)
                    js = list(range(nb - 1, -1, -1))
                    for j in (reversed(js) if inverse else js):
                        b.cswap(sb[r], y1[j], y1[j + m])
                if sbp is None:
                    sbits_load(sb); b.free(sb)
                return
            for r in ((0, 1, 2, 3) if inverse else (3, 2, 1, 0)):
                if self.packflags:  # trimmed lane: value bits (incl. the 2^fy bit) + max shift reachable with bit r set (s <= 10)
                    L = self.widths[0] + max(v & ~((1 << r) - 1) for v in range(11) if v >> r & 1)
                if getattr(self, 'zshift', False):  # top 2^r bits of the lane are known zero: shift, not rotate
                    m = 2**r
                    js = list(range(L - m - 1, -1, -1))
                    for j in (reversed(js) if inverse else js):
                        b.cswap(sb[r], y1[j], y1[j + m])
                elif inverse:
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
                if getattr(self, 'droprot', 0) <= j < F:  # --droprot m: lowest m bits not phased (error <= (2^m-1) 2^-F turns)
                    b.z_pow(y1[j], Fraction(2)**(j - F + 1))
        with b.mark('denormalize_inv'):
            denorm(True)
        if dt: b.x(topq[0])
        b.free(y1[self.widths[0] - dt:])
        with b.mark('horner_inv'):
            horner(True)
        with b.mark('lookup_inv'):
            b.del_lookup(table=table, address=address, target=target)
        for r in regs + ([pad] if self.pad else []) + list(carry.values()):
            b.free(r)
        if getattr(self, 'binnorm', False):
            with b.mark('normalize_inv'):
                binnorm.normalize(b, x, sbp, True)
            b.free(sbp)
        else:
            if sbp is not None:
                flags = b.alloc_qubits(N_P); flagpack.unpack(b, flags, sbp); b.free(sbp)
            with b.mark('normalize_inv'):
                _normalize(b, True, x, flags)
            b.free(flags)
        return b.finish_circuit()


def group_ok(d, j, a, LA):
    """Exact check over all x_norm: rows i<a of step j summed into an (LA+2)-bit signed window must not wrap."""
    xn = np.arange(2**20, 2**22, dtype=np.int64)
    d.model(xn, d.coefs)
    D, g = d.D, d.guards
    sh = g[j] - g[j - 1]
    init, _ = d._steps[j]
    # recompute src register value regs[j] at the time of step j
    A = xn >> D; t = xn & ((1 << D) - 1)
    regs = [c[A].copy() for c in d.coefs]
    for jj in range(d.deg, j, -1):
        regs[jj - 1] = d._steps[jj][1]
    src = regs[j]
    part = np.zeros_like(xn)
    for i in range(a):
        e = i - D - sh
        sg = 2 * ((t >> i) & 1) - 1
        v = src >> -e if e < 0 else src << e
        if e < 0 and j in getattr(d, 'round', ()):
            v = v + ((src >> (-e - 1)) & 1)
        part += sg * v
    q = (init & ((1 << LA) - 1)) - part
    return bool(q.min() >= -2**(LA + 1) and q.max() < 2**(LA + 1)), int(q.min()), int(q.max())


def main(Design=Design):
    import argparse, hashlib
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=9); ap.add_argument('--deg', type=int, default=2)
    ap.add_argument('--fy', type=int, default=31); ap.add_argument('--guards', default=None)
    ap.add_argument('--out', default=None); ap.add_argument('--cadd', action='store_true')
    ap.add_argument('--binshift', action='store_true'); ap.add_argument('--rangeq', action='store_true')
    ap.add_argument('--packflags', action='store_true')
    ap.add_argument('--pad', type=int, default=0)
    ap.add_argument('--clamp', action='store_true')
    ap.add_argument('--binnorm', action='store_true')
    ap.add_argument('--zshift', action='store_true')
    ap.add_argument('--maxq', type=int, default=0)
    ap.add_argument('--droptop', action='store_true')
    ap.add_argument('--droprot', type=int, default=0)
    ap.add_argument('--smallfirst', action='store_true')
    ap.add_argument('--foldadd', action='store_true')
    ap.add_argument('--round', default='')
    ap.add_argument('--gadd', action='store_true')
    ap.add_argument('--groups', default='')
    a = ap.parse_args()
    if a.round: Design.round = tuple(int(v) for v in a.round.split(','))  # class-level: the coefficient search in __init__ must see it
    d = Design(a.k, a.deg, a.fy, guards=[int(v) for v in a.guards.split(',')] if a.guards else None, cadd=a.cadd, binshift=a.binshift, rangeq=a.rangeq, packflags=a.packflags)
    d.pad = a.pad
    d.clamp = a.clamp
    d.binnorm = a.binnorm
    d.zshift = a.zshift
    d.maxq = a.maxq
    d.droptop = a.droptop
    d.droprot = a.droprot
    d.smallfirst = a.smallfirst
    d.foldadd = a.foldadd
    d.gadd = a.gadd
    d.groups = {int(g.split(':')[0]): (int(g.split(':')[1]), int(g.split(':')[2])) for g in a.groups.split(',') if g}
    e = d.calibrate()
    print('L', d.choose_L())
    for j, (ga, gl) in d.groups.items():
        ok = group_ok(d, j, ga, gl); print('group', j, ga, gl, ok); assert ok[0]
    print(f'k={a.k} deg={a.deg} fy={a.fy} guards={d.guards} widths={d.widths} max rel err 2^{math.log2(e):.2f}')
    c = d.build()
    print('qubits', c.num_qubits, 'toffoli(static)', c.operation_statistics().num_toffoli_like)
    if a.out:
        c.to_file(a.out, format='kmb')
        print(a.out, hashlib.sha256(open(a.out, 'rb').read()).hexdigest()[:16])





import lutpoly7 as _l7
class SDesign(_l7.Search, Design):
    pass

if __name__ == '__main__':
    SDesign.search = True
    main(SDesign)
