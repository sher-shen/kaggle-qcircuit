"""Formal window test on stage_xag.py output: for consecutive AND windows W (k=2..K, no intra-window dependence),
rank r of the consumers' W-projection; if r < k, search the r-dim needed space: for r=1 the symplectic rank of
Q = sum c_i u_i v_i gives the minimal product count (formal); report windows where r/2 < |supp c| (gain).
Also reports the r>=2 windows count.  Usage: stage_qform.py stage.json [K]"""
import json, sys
d = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 12
nv0 = d['nv0']
A = [(int(a, 16), ca, int(b, 16), cb) for a, ca, b, cb in d['ands']]
cons = [(j, int(m, 16)) for j, m in d['cons']]
N = len(A); NV = nv0 + N
def rank_rows(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r
byand = {}
for ci, (j, m) in enumerate(cons):
    mm = m >> nv0; t = 0
    while mm:
        if mm & 1: byand.setdefault(t, []).append(ci)
        mm >>= 1; t += 1
def proj(W):
    Ws = set(W); vecs = set()
    idx = sorted(set(ci for w in W for ci in byand.get(w, [])))
    for j, m in (cons[ci] for ci in idx):
        if j in Ws: continue
        v = 0
        for t, w in enumerate(W):
            if (m >> (nv0 + w)) & 1: v |= 1 << t
        if v: vecs.add(v)
    return vecs
def symp_rank(terms):
    rows = {}
    for u, v in terms:
        for i in range(NV):
            if (u >> i) & 1: rows[i] = rows.get(i, 0) ^ v
            if (v >> i) & 1: rows[i] = rows.get(i, 0) ^ u
    return rank_rows([r & ~(1 << i) for i, r in rows.items()])
stats = {}; gains = []
import itertools
SPAN = int(sys.argv[3]) if len(sys.argv) > 3 else 0
def windows():
    if not SPAN:
        for k in range(2, K + 1):
            for s in range(N - k + 1): yield list(range(s, s + k))
    else:  # all subsets of size 2..K (K<=4) inside a span of SPAN consecutive ANDs, containing the first one
        for s in range(N):
            rest = range(s + 1, min(N, s + SPAN))
            for kk in range(1, K):
                for c in itertools.combinations(rest, kk): yield [s] + list(c)
for W in windows():
        k = len(W); s = W[0]
        wm = sum(1 << (nv0 + w) for w in W)
        if any((A[w][0] | A[w][2]) & wm for w in W): continue
        P = proj(W); r = rank_rows(list(P))
        stats[(k, r)] = stats.get((k, r), 0) + 1
        if r < k and r <= 4:
            # basis of the needed space, then best basis by greedy over all nonzero elements sorted by symplectic rank
            bs = []
            for v in P:
                if rank_rows(bs + [v]) > len(bs): bs.append(v)
            el = []
            for msk in range(1, 1 << r):
                c = 0
                for t in range(r):
                    if (msk >> t) & 1: c ^= bs[t]
                terms = [(A[W[t]][0], A[W[t]][2]) for t in range(k) if (c >> t) & 1]
                el.append((symp_rank(terms) // 2, c))
            el.sort(); chosen = []; cost = 0
            for pc, c in el:
                if rank_rows(chosen + [c]) > len(chosen): chosen.append(c); cost += pc
            if cost < k: gains.append((k - cost, s, k, r, cost, tuple(W)))
print('N', N, '(k, rank): count', dict(sorted(stats.items())))
oi = d.get('opidx')
print('formal gains (gain, start, k, r, cost, first_op)', [g + (oi[g[1]] if oi else None,) for g in sorted(gains, reverse=True)][:30])
