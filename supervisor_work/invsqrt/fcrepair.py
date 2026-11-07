"""--freecarry support (supervisor, 2026-11-07): parity-aware per-segment coefficient repair.

After a Horner fold `hi -= c` the window sign bit c satisfies c = bit0(hi') XOR bit0(hi0(A)), and for the
group window cA = bit_LA(acc') XOR bit_LA(loaded(A)). If those classical bits equal an affine GF(2) function
p(A) = parity(A & mask) ^ cst of the address, CX gates clear c / cA, so the qubit is freed right after its fold
and re-created (same CXs) just before the inverse fold. The per-segment offset k in {0,-1} flips that parity,
so a segment is fine if the k matching p(A) is feasible. Segments where it is not are repaired by choosing
another (d1, d2, a0-shift) candidate of the lutpoly16 search whose weighted slack is still >= the global
minimum of the unrepaired design (so the rotation budget does not shrink) and whose windows stay feasible.
"""
import numpy as np, sys

MAX_X = 3 * (2**10 - 2)**2


def _seg_minmax(v, A, nseg):
    mn = np.full(nseg, 2**62); mx = np.full(nseg, -2**62)
    np.minimum.at(mn, A, v); np.maximum.at(mx, A, v)
    return mn, mx


def _feas(low, A, W, nseg):
    mn, mx = _seg_minmax(low, A, nseg)
    return (mn >= -2**W) & (mx < 2**W), (mn >= 0) & (mx < 2**(W + 1))


def _affine_solve(req_sets, nseg=512):
    """req_sets[A] subset of {0,1} (bitmask: 1 -> parity 0 allowed, 2 -> parity 1 allowed; 3 any).
    Return (mask, cst) with parity(A & mask)^cst allowed for all A, or None."""
    forced = [A for A in range(nseg) if req_sets[A] in (1, 2)]
    if any(req_sets[A] == 0 for A in range(nseg)): return None
    rows = []
    for A in forced:
        rows.append(sum(((A >> i) & 1) << i for i in range(9)) | (1 << 9) | ((0 if req_sets[A] == 1 else 1) << 10))
    # gaussian elimination over 10 unknowns (bits 0..9), rhs bit 10
    piv = {}
    for r in rows:
        for c in range(10):
            if not (r >> c) & 1: continue
            if c in piv: r ^= piv[c]
            else:
                piv[c] = r; break
        else:
            if (r >> 10) & 1: return None
    sol = 0
    for c in sorted(piv, reverse=True):
        r = piv[c]; v = (r >> 10) & 1
        for c2 in range(c + 1, 10):
            if (r >> c2) & 1: v ^= (sol >> c2) & 1
        sol |= v << c
    return sol & 511, (sol >> 9) & 1


def repair(d, Wfix, j2=2, jg=1, use2=True, useA=True, use1=False):
    """d: design after calibrate (d.coefs set, d.L computed by choose_L1). Modifies d.coefs/kc/kA, sets d.fc."""

    xn = np.arange(2**20, 2**22, dtype=np.int64)
    s = np.where(xn <= MAX_X, 0, np.where(xn % 4 == 0, 1, -1)); keep = s >= 0
    D, nseg, fy = d.D, 2**d.k, d.fy
    A = xn >> D
    exact = 2.0**fy / np.sqrt(xn / 2.0**20); tol = 2.0**-24 * exact; w = np.where(keep, 2.0**np.maximum(s, 0), 0)
    grp = d.groups.get(jg); LA, ga = grp[1], grp[0]
    W2, W1 = d.L[j2], d.L[jg]
    base = [c.copy() for c in d.coefs]
    def slack_of(y):
        sl = np.where(keep, w * (tol - np.abs(d._drop(y, np.maximum(s, 0)) - exact)), np.inf)
        m = np.full(nseg, np.inf); np.minimum.at(m, A, sl); return m
    thr = slack_of(d.model(xn, base)).min() - 1e-9
    R, DS = 3, 4
    cands = []  # per candidate: arrays over segments
    for d1 in range(-R, R + 1):
        for d2 in range(-R, R + 1):
            c = [base[0], base[1] + d1, base[2] + d2]
            if (c[1] < 0).any() or (c[2] < 0).any(): continue
            sw = d.widths; d.widths = [62] * len(sw)
            try: y = d.model(xn, c)
            finally: d.widths = sw
            regok = np.ones(nseg, bool)
            for jj in d._steps:
                mn_, mx_ = _seg_minmax(d._steps[jj][1], A, nseg); regok &= (mn_ >= 0) & (mx_ < 2**sw[jj - 1])
            for jj in range(len(c)):
                cc = np.zeros(nseg, np.int64); cc[:len(c[jj])] = c[jj]; regok &= (cc >= 0) & (cc < 2**sw[jj])
            r_init, r_fin = d._steps[j2]
            k0_2, k1_2 = _feas((r_init & ((1 << W2) - 1)) - (r_init - r_fin), A, W2, nseg)
            par2 = (c[1] >> W2) & 1
            partA = d.part_A(xn, jg, ga)
            a0x = c[0][A]
            for dd in range(-DS, DS + 1):
                yy = y - dd
                sl = slack_of(yy)
                _, ymax = _seg_minmax(yy, A, nseg)
                okc = ymax <= 2**fy - 1
                a0 = a0x - dd
                k0_1, k1_1 = _feas((a0 & ((1 << W1) - 1)) - (a0 - yy), A, W1, nseg)
                k0_A, k1_A = _feas((a0 & ((1 << LA) - 1)) - partA, A, LA, nseg)
                parA = ((c[0] - dd) >> LA) & 1
                par1 = ((c[0] - dd) >> W1) & 1
                ok = regok & okc & (sl >= thr) & (k0_1 | k1_1) & (k0_2 | k1_2) & (k0_A | k1_A)
                # allowed parities: k=0 -> par, k=-1 -> par^1
                al2 = np.where(k0_2, 1 << par2, 0) | np.where(k1_2, 1 << (par2 ^ 1), 0)
                alA = np.where(k0_A, 1 << parA, 0) | np.where(k1_A, 1 << (parA ^ 1), 0)
                al1 = np.where(k0_1, 1 << par1, 0) | np.where(k1_1, 1 << (par1 ^ 1), 0)
                cands.append(dict(d1=d1, d2=d2, dd=dd, ok=ok, sl=sl, al2=al2, alA=alA, al1=al1))
    used = np.zeros(nseg, bool); used[np.unique(A)] = True
    print(f'fcrepair: {len(cands)} candidates, slack thr {thr:.4f}', file=sys.stderr)
    # per segment: set of (p2, pA, p1) triples supported (as 8-bit mask)
    sup = np.zeros(nseg, dtype=np.int64)
    for cd in cands:
        for p2 in (0, 1):
            for pA in (0, 1):
                for p1 in (0, 1):
                    m = cd['ok'] & (((cd['al2'] >> p2) & 1) | (not use2)).astype(bool) & (((cd['alA'] >> pA) & 1) | (not useA)).astype(bool) & (((cd['al1'] >> p1) & 1) | (not use1)).astype(bool)
                    sup |= np.where(m, 1 << (p2 * 4 + pA * 2 + p1), 0)
    sup[~used] = 255
    print('fcrepair: segments with no candidate', int((sup == 0).sum()), file=sys.stderr)
    par = np.array([[bin(a & m).count('1') & 1 for a in range(nseg)] for m in range(512)])
    best = None
    for m2 in (range(512) if use2 else [0]):
        for c2 in ((0, 1) if use2 else (0,)):
            p2 = par[m2] ^ c2 if use2 else np.zeros(nseg, int)
            # allowed (pA,p1) per seg given p2
            sub = (sup >> (4 * p2)) & 15
            if (sub == 0).any(): continue
            reqA = np.zeros(nseg, int)
            for pA in (0, 1):
                reqA |= np.where(((sub >> (2 * pA)) & 3) != 0, 1 << pA, 0)
            if useA:
                solA = _affine_solve(list(reqA))
                if solA is None: continue
                pA = par[solA[0]] ^ solA[1]
            else:
                solA = (0, 0); pA = np.zeros(nseg, int)
            if use1:
                sub1 = (sub >> (2 * pA)) & 3
                sol1 = _affine_solve(list(sub1))
                if sol1 is None: continue
            else:
                sol1 = (0, 0)
            best = ((m2, c2), solA, sol1); break
        if best: break
    if best is None:
        print('fcrepair: no affine parity assignment', file=sys.stderr); return False
    (m2, c2), (mA, cA), (m1, c1) = best
    p2 = par[m2] ^ c2; pA = par[mA] ^ cA; p1 = par[m1] ^ c1
    print(f'fcrepair: masks step2 {best[0]} group {best[1]} step1 {best[2]}', file=sys.stderr)
    newc = [c.copy() for c in base]; choice = {}
    nchg = 0
    for Aseg in np.where(used)[0]:
        bestc = None
        for cd in cands:
            if not cd['ok'][Aseg]: continue
            if use2 and not (cd['al2'][Aseg] >> p2[Aseg]) & 1: continue
            if useA and not (cd['alA'][Aseg] >> pA[Aseg]) & 1: continue
            if use1 and not (cd['al1'][Aseg] >> p1[Aseg]) & 1: continue
            if bestc is None or cd['sl'][Aseg] > bestc['sl'][Aseg] + 1e-12 or (abs(cd['sl'][Aseg] - bestc['sl'][Aseg]) <= 1e-12 and (cd['d1'], cd['d2'], cd['dd']) == (0, 0, 0)):
                bestc = cd
        assert bestc is not None
        if (bestc['d1'], bestc['d2'], bestc['dd']) != (0, 0, 0): nchg += 1
        newc[0][Aseg] = base[0][Aseg] - bestc['dd']; newc[1][Aseg] = base[1][Aseg] + bestc['d1']; newc[2][Aseg] = base[2][Aseg] + bestc['d2']
    print(f'fcrepair: {nchg} segments changed', file=sys.stderr)
    d.coefs = newc
    d.model(xn, d.coefs)
    # offsets matching the parities
    r_init, r_fin = d._steps[j2]
    k0, k1 = _feas((r_init & ((1 << W2) - 1)) - (r_init - r_fin), A, W2, nseg)
    par2 = (d.coefs[1] >> W2) & 1
    if use2:
        kc2 = np.where(par2 == p2, 0, -1); assert (~used | np.where(kc2 == 0, k0, k1)).all()
        d.kc[j2] = np.where(used, kc2, 0).astype(np.int64)
    else:
        d.kc[j2] = d.seg_k((r_init & ((1 << W2) - 1)) - (r_init - r_fin), A, W2, nseg)
    a0, y = d.coefs[0][A], d._steps[jg][1]
    k0, k1 = _feas((a0 & ((1 << W1) - 1)) - (a0 - y), A, W1, nseg)
    par1 = (d.coefs[0] >> W1) & 1
    if use1:
        kc1 = np.where(par1 == p1, 0, -1); assert (~used | np.where(kc1 == 0, k0, k1)).all()
        d.kc[jg] = np.where(used, kc1, 0).astype(np.int64)
    else:
        d.kc[jg] = d.seg_k((a0 & ((1 << W1) - 1)) - (a0 - y), A, W1, nseg)
    k0, k1 = _feas((a0 & ((1 << LA) - 1)) - d.part_A(xn, jg, ga), A, LA, nseg)
    parA = (d.coefs[0] >> LA) & 1
    if useA:
        kA = np.where(parA == pA, 0, -1); assert (~used | np.where(kA == 0, k0, k1)).all()
        d.kA[jg] = np.where(used, kA, 0).astype(np.int64)
    else:
        d.kA[jg] = d.seg_k((a0 & ((1 << LA) - 1)) - d.part_A(xn, jg, ga), A, LA, nseg)
    d.fc = {}
    if use2: d.fc[('c', j2)] = (m2, c2)
    if useA: d.fc[('A', jg)] = (mA, cA)
    if use1: d.fc[('c', jg)] = (m1, c1)
    return True


def solve_feat(F, allowed):
    """F: (nseg, nf) 0/1 feature matrix, allowed[A] in {0,1,2,3} (bit p set: parity p ok).
    Return (coef list of feature indices, cst) with parity(F[A] . coef) ^ cst allowed for all A, else None."""
    nseg, nf = F.shape
    if (allowed == 0).any(): return None
    piv = {}
    for A in range(nseg):
        if allowed[A] == 3: continue
        rhs = 0 if allowed[A] == 1 else 1
        r = 0
        for i in range(nf):
            if F[A, i]: r |= 1 << i
        r |= 1 << nf; r |= rhs << (nf + 1)
        for c in range(nf + 1):
            if not (r >> c) & 1: continue
            if c in piv: r ^= piv[c]
            else: piv[c] = r; break
        else:
            if (r >> (nf + 1)) & 1: return None
    sol = 0
    for c in sorted(piv, reverse=True):
        r = piv[c]; v = (r >> (nf + 1)) & 1
        for c2 in range(c + 1, nf + 1):
            if (r >> c2) & 1: v ^= (sol >> c2) & 1
        sol |= v << c
    return [i for i in range(nf) if (sol >> i) & 1], (sol >> nf) & 1
