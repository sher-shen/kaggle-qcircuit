"""Cheap exact lower bound for the chain test (supervisor 2026-11-09 00 UTC).
For a dump (E, pairs, n) let O = vertices touched by no relation K.  Every entry of y = Q0 + K l in a column of O is fixed (= Q0),
so rank(y) >= rank(Q0[:, O]) and rank(y) >= rank(Q0[O, O]) ... ; also print the in-block/out-of-block split of Q0.
If rank(Q0[:, O]) > 2R the L -> R merge is impossible (exact, relative to the sampled relations)."""
import sys, re, os, numpy as np
def rank(M):
    M = M.copy(); r = 0; R_, C = M.shape
    for c in range(C):
        piv = np.nonzero(M[r:, c])[0]
        if len(piv) == 0: continue
        p = r + piv[0]; M[[r, p]] = M[[p, r]]; rows = np.nonzero(M[:, c])[0]; rows = rows[rows != r]; M[rows] ^= M[r]; r += 1
        if r == R_: break
    return r
for fn in sys.argv[1:]:
    d = np.load(fn); E = d['E'].astype(bool); P = [tuple(map(int, p)) for p in d['pairs']]; n = int(d['n'])
    L = int(re.search(r'-L(\d+)_', fn).group(1))
    touched = E[:, 1:].any(1); deg = np.zeros(n, int)
    for t in np.nonzero(touched)[0]: a, b = P[t]; deg[a] += 1; deg[b] += 1
    O = [a for a in range(n) if deg[a] == 0]; Bk = [a for a in range(n) if deg[a] > 0]
    Q = np.zeros((n, n), bool)
    for t in np.nonzero(E[:, 0])[0]: a, b = P[t]; Q[a, b] = Q[b, a] = True
    rQ = rank(Q); rO = rank(Q[:, O]) if O else 0
    q0v = sorted({a for t in np.nonzero(E[:, 0])[0] for a in P[t]})
    verdict = 'REJECT(exact)' if rO > 2 * (L - 1) else 'open'
    print(f'{os.path.basename(fn)} L={L} n={n} block={len(Bk)} out={len(O)} rank(Q0)={rQ} rank(Q0[:,out])={rO} Q0verts={len(q0v)} in-block={len(set(q0v)&set(Bk))} -> {verdict} for {L}->{L-1}', flush=True)
