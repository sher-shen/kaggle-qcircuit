"""Extension of stage_qform.py ("one AND away"): for windows W of 2..K independent ANDs whose consumer projection has
rank 1 (only the XOR sum is used), test whether Q_W + A_j (+affine) has symplectic rank 2 (= one product) for some
other AND j of the stage (anywhere, not only inside a span).  Then the k ANDs become 1 CCX + a CX copy of A_j, if A_j is
available on some wire at that moment (must be checked by hand / with the verifier).  Usage: stage_qform_plus.py st.json [K] [SPAN]"""
import json, sys, itertools
d = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 2; SPAN = int(sys.argv[3]) if len(sys.argv) > 3 else 12
nv0 = d['nv0']; A = [(int(a, 16), int(b, 16)) for a, ca, b, cb in d['ands']]
cons = [(j, int(m, 16)) for j, m in d['cons']]; N = len(A); NV = nv0 + N; oi = d['opidx']
byand = {}
for ci, (j, m) in enumerate(cons):
    mm = m >> nv0; t = 0
    while mm:
        if mm & 1: byand.setdefault(t, []).append(ci)
        mm >>= 1; t += 1
def rank_rows(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r
def symp(terms):
    rows = {}
    for u, v in terms:
        u &= (1 << 10**6) - 1; 
        x = u
        while x:
            i = x.bit_length() - 1; rows[i] = rows.get(i, 0) ^ v; x ^= 1 << i
        x = v
        while x:
            i = x.bit_length() - 1; rows[i] = rows.get(i, 0) ^ u; x ^= 1 << i
    return rank_rows([r & ~(1 << i) for i, r in rows.items()])
def proj(W):
    Ws = set(W); vecs = set()
    for ci in sorted(set(ci for w in W for ci in byand.get(w, []))):
        j, m = cons[ci]
        if j in Ws: continue
        v = 0
        for t, w in enumerate(W):
            if (m >> (nv0 + w)) & 1: v |= 1 << t
        if v: vecs.add(v)
    return vecs
hits = []
for s in range(N):
    for kk in range(1, K):
        for c in itertools.combinations(range(s + 1, min(N, s + SPAN)), kk):
            W = [s] + list(c); wm = sum(1 << (nv0 + w) for w in W)
            if any((A[w][0] | A[w][1]) & wm for w in W): continue
            P = proj(W)
            if P != {(1 << len(W)) - 1}: continue
            terms = [A[w] for w in W]
            base = symp(terms) // 2
            if base < len(W): hits.append(('direct', base, [oi[w] for w in W])); continue
            for j in range(N):
                if j in W: continue
                if symp(terms + [A[j]]) // 2 <= len(W) - 1 - 1 + 1 and symp(terms + [A[j]]) // 2 < len(W):
                    hits.append(('plusAND', symp(terms + [A[j]]) // 2, [oi[w] for w in W], oi[j]))
print('N', N, 'hits', len(hits))
for h in hits[:60]: print(h)
