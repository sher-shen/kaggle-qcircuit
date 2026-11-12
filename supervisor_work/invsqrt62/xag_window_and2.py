"""Like xag_window_and1.py, but candidates g,h range over span(const, operands u_i, v_i of the window ANDs).
For each rank-1 window W (k=2..K) checks whether f = sum c_i a_i = AND(g,h) + l with l in span(const, inputs, ANDs < s).
Usage: xag_window_and2.py xag.json [K]"""
import json, sys, itertools, numpy as np
exec(open(__file__.replace('xag_window_and2.py', 'xag_window_and1.py')).read().split("aff = np.array")[0])
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
tot = 0; hits = []
for k in range(2, K + 1):
    for s in range(N - k + 1):
        W = list(range(s, s + k)); P = proj(W)
        if len(P) != 1: continue
        c = next(iter(P))
        ops = []
        for w in W: ops += [ev(A[w][0], A[w][1]), ev(A[w][2], A[w][3])]
        # basis of span(const, ops)
        gens = [np.ones(256, np.uint8)] + ops
        span = {np.zeros(256, np.uint8).tobytes(): np.zeros(256, np.uint8)}
        for g in gens:
            new = {}
            for v in span.values():
                w2 = v ^ g; new[w2.tobytes()] = w2
            span.update(new)
        S = np.array(list(span.values()))
        if len(S) > 4096: continue
        tot += 1
        iu = np.triu_indices(len(S), 1)
        f = np.zeros(256, np.uint8)
        for t in range(k):
            if (c >> t) & 1: f ^= T[9 + s + t]
        found = 0
        for b0 in range(0, len(iu[0]), 200000):
            P2 = (S[iu[0][b0:b0+200000]] & S[iu[1][b0:b0+200000]]) ^ f[None, :]
            Cc = coords(P2)
            ok = (Cc[:, 186:].sum(1) == 0) & (Cc[:, 9 + s:186].sum(1) == 0)
            found += int(ok.sum())
        if found: hits.append((s, k, bin(c).count('1'), found))
    print('k', k, 'windows tested', tot, 'hits so far', len(hits), flush=True)
print('hits', hits[:40])
