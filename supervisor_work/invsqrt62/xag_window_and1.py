"""Functional test: for each consecutive window W (k>=2) of the coeff_lookup XAG whose consumers see only one combination
f = sum_{i in W} c_i a_i, look for ONE product p = AND(g, h) with f + p in span(const, inputs, ANDs before W).
Candidates: g,h affine over the 8 inputs; g = a_j (j<s) [+1], h affine over inputs; g = a_j, h = a_l.
Truth-table coordinates over the basis {const, inputs, 177 ANDs, completion}.  Usage: xag_window_and1.py xag.json [K]"""
import json, sys, numpy as np
d = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 12
A = [(int(a, 16), ca, int(b, 16), cb) for a, ca, b, cb in d['ands']]
O = [(int(m, 16), c) for m, c in d['outs']]
N = len(A)
X = np.arange(256)
T = [np.ones(256, np.uint8)] + [((X >> i) & 1).astype(np.uint8) for i in range(8)]
def ev(m, c):
    r = np.full(256, c, np.uint8); k = 0
    while m:
        if m & 1: r ^= T[1 + k]
        m >>= 1; k += 1
    return r
for a, ca, b, cb in A: T.append(ev(a, ca) & ev(b, cb))
B = np.array(T, np.uint8)  # 186 x 256
# completion to full basis
def gf2_inv_basis(B):
    rows = [r.copy() for r in B]
    n = 256
    # extend with unit vectors
    M = np.concatenate([B, np.eye(n, dtype=np.uint8)])
    # greedy pick independent rows
    sel = []; red = []; piv = []
    for i, r in enumerate(M):
        v = r.copy()
        for p, rv in zip(piv, red):
            if v[p]: v ^= rv
        nz = np.nonzero(v)[0]
        if len(nz) == 0: continue
        piv.append(nz[0]); red.append(v); sel.append(i)
        if len(sel) == n: break
    return M[sel], sel
Bf, sel = gf2_inv_basis(B)
assert sel[:186] == list(range(186)), 'not independent'
# solve coords: t = coords @ Bf  -> coords = t @ inv(Bf)
def gf2_inv(M):
    n = M.shape[0]; aug = np.concatenate([M.copy(), np.eye(n, dtype=np.uint8)], 1)
    r = 0
    for c in range(n):
        p = next(i for i in range(r, n) if aug[i, c])
        aug[[r, p]] = aug[[p, r]]
        for i in range(n):
            if i != r and aug[i, c]: aug[i] ^= aug[r]
        r += 1
    return aug[:, n:]
Inv = gf2_inv(Bf).astype(np.float32)
def coords(P):  # P: m x 256 uint8
    out = []
    for s in range(0, len(P), 20000):
        out.append((P[s:s+20000].astype(np.float32) @ Inv).astype(np.int64) & 1)
    return np.concatenate(out).astype(np.uint8)
aff = np.array([ev(m, c) for m in range(256) for c in (0, 1)], np.uint8)  # 512 affine input functions
cands = []; desc = []
iu = np.triu_indices(512, 1)
P1 = aff[iu[0]] & aff[iu[1]]; cands.append(P1); desc += [('aa', int(i), int(j)) for i, j in zip(*iu)]
for j in range(N):
    for cj in (0, 1):
        g = T[9 + j] ^ cj
        cands.append(g[None, :] & aff); desc += [('Aa', j, cj, q) for q in range(512)]
C = coords(np.concatenate(cands))
print('candidates', len(C))
# AND index of each candidate's highest AND dependency (for g=a_j: j)
cons = []
for j, (a, ca, b, cb) in enumerate(A): cons += [(j, a), (j, b)]
for m, c in O: cons.append((-1, m))
def proj(W):
    Ws = set(W); vecs = set()
    for j, m in cons:
        if j in Ws: continue
        v = 0
        for t, w in enumerate(W):
            if (m >> (8 + w)) & 1: v |= 1 << t
        if v: vecs.add(v)
    return vecs
def rank1(vecs):
    vs = list(vecs)
    return len(vs) == 1
inspan = C[:, 186:].sum(1) == 0
print('candidates in span(G)', int(inspan.sum()))
Cs = C[inspan]; Ds = [desc[i] for i in np.nonzero(inspan)[0]]
hits = []
nw = 0
for k in range(2, K + 1):
    for s in range(N - k + 1):
        W = list(range(s, s + k)); P = proj(W)
        if len(P) != 1: continue
        nw += 1
        c = next(iter(P))
        target = np.zeros(177, np.uint8)
        for t in range(k):
            if (c >> t) & 1: target[s + t] = 1
        # coords on ANDs >= s must equal target on [s, N)
        Ac = Cs[:, 9:186]
        ok = np.all(Ac[:, s:] == target[s:], 1)
        # candidate's own operands must be before s
        for i in np.nonzero(ok)[0]:
            dsc = Ds[i]
            if dsc[0] == 'Aa' and dsc[1] >= s: continue
            hits.append((s, k, int(target.sum()), dsc))
print('rank-1 windows', nw, 'hits', len(hits))
for h in hits[:40]: print(h)
