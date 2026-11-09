"""Self-test for star_scan.py: plant Q0 = v^w1 + u^w + K l into a dump (u, w, w1 random on the touched block).
Usage: star_plant.py dump.npz out.npz seed  -> prints v"""
import sys, numpy as np
d = np.load(sys.argv[1]); E = d['E'].astype(bool).copy(); P = d['pairs']; n = int(d['n']); rng = np.random.default_rng(int(sys.argv[3]))
t = E[:, 1:].any(1); blk = sorted({int(a) for i in np.nonzero(t)[0] for a in P[i]})
v = int(rng.choice(blk)); u, w, w1 = (np.zeros(n, bool) for _ in range(3))
for a in blk: u[a], w[a] = rng.random(2) < 0.5
w1[:] = rng.random(n) < 0.5
l = rng.random(E.shape[1] - 1) < 0.5
for i, (a, b) in enumerate(P):
    a, b = int(a), int(b); x = (u[a] & w[b]) ^ (u[b] & w[a])
    if a == v: x ^= w1[b]
    if b == v: x ^= w1[a]
    E[i, 0] = x ^ bool(np.count_nonzero(E[i, 1:] & l) & 1)
np.savez_compressed(sys.argv[2], E=E.astype(np.uint8), pairs=P, n=n); print(v)
