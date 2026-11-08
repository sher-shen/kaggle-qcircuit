"""For consecutive AND windows W whose consumers see only a 1-dim projection (sum of ANDs with coeffs c),
compute the formal quadratic form Q = sum_i c_i u_i v_i (u_i, v_i affine masks over earlier signals) and
its symplectic rank r: Q can be written with r/2 products of affine forms (+ affine part). Gain = |supp c| - r/2.
Windows with intra-window dependence are skipped.  Usage: xag_qform.py xag.json [K]"""
import json, sys
d = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 12
A = [(int(a, 16), ca, int(b, 16), cb) for a, ca, b, cb in d['ands']]
O = [(int(m, 16), c) for m, c in d['outs']]
N = len(A); NV = 8 + N
cons = []
for j, (a, ca, b, cb) in enumerate(A): cons += [(j, a), (j, b)]
for m, c in O: cons.append((-1, m))
def rank_rows(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r, basis
def proj(W):
    Ws = set(W); vecs = set()
    for j, m in cons:
        if j in Ws: continue
        v = 0
        for t, w in enumerate(W):
            if (m >> (8 + w)) & 1: v |= 1 << t
        if v: vecs.add(v)
    return vecs
def symp_rank(terms):
    # terms: list of (u, v) masks with constants ignored (constants give linear terms)
    # alternating matrix rows over NV vars
    rows = [0] * NV
    for u, v in terms:
        for i in range(NV):
            if (u >> i) & 1: rows[i] ^= v
            if (v >> i) & 1: rows[i] ^= u
    # remove diagonal (alternating: diag zero); rows[i] bit i from u_i v_i -> square = linear
    for i in range(NV): rows[i] &= ~(1 << i)
    return rank_rows([r for r in rows if r])[0]
best = []
for k in range(2, K + 1):
    for s in range(N - k + 1):
        W = list(range(s, s + k))
        wm = sum(1 << (8 + w) for w in W)
        if any((A[w][0] | A[w][2]) & wm for w in W): continue
        P = proj(W)
        r, _ = rank_rows(list(P))
        if r != 1: continue
        c = next(iter(P))
        terms = [(A[W[t]][0], A[W[t]][2]) for t in range(k) if (c >> t) & 1]
        # constants: (u+cu)(v+cv) = uv + cu v + cv u + cu cv: linear extra, ignore
        sr = symp_rank(terms)
        gain = len(terms) - sr // 2
        best.append((gain, s, k, len(terms), sr))
best.sort(reverse=True)
print('rank-1 windows', len(best)); print('top', best[:15])
print('positive gain', [b for b in best if b[0] > 0][:30])
