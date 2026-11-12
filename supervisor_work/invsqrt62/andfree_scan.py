"""andfree_scan.py ops.json wins.npy [nx] [reps]: at the start and middle of every 62-wide window, look for a live wire
w with w = (a&b) ^ affine(live \\ {w}) for live wires a,b (either polarity; absorbed into the affine part).
Such a wire could be uncomputed by measurement (0 Toffoli) and recomputed later with 1 Toffoli, freeing one line
for that stretch. Each x is repeated `reps` times so HMR-outcome histories are sampled."""
import sys, json, numpy as np
d = json.load(open(sys.argv[1])); W = np.load(sys.argv[2])
nx = int(sys.argv[3]) if len(sys.argv) > 3 else 3000; reps = int(sys.argv[4]) if len(sys.argv) > 4 else 3
rng0 = np.random.default_rng(11); MAXX = 3 * (2**10 - 2)**2
xs = np.unique(np.concatenate([np.arange(1, 1500), rng0.integers(1, MAXX + 1, nx)])).astype(np.int64)
xs = np.repeat(xs, reps)
stops = sorted(set([int(a) for a, b in W] + [int((a + b) // 2) for a, b in W]))
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']; N = len(xs); rng = np.random.default_rng(3)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
snaps = {}; si = 0
for i, o in enumerate(ops):
    while si < len(stops) and stops[si] == i: snaps[i] = (q.copy(), len(stack)); si += 1
    if si >= len(stops): break
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act
    a = o[1:]
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP':
        u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
    elif k == 'SWAP':
        u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
    elif k in ('HMR', 'R'):
        r = rng.random(N) < 0.5
        if k == 'HMR': bb = B(a[1]); bb[m] = r[m]
        q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE0': B(a[0])[m] = False
    elif k == 'BIT_STORE1': B(a[0])[m] = True
def gf2_solve_all(M, T):
    """M: N x n (0/1), T: N x m. Return mask of columns of T in colspace(M) and coefficient matrix."""
    A = np.concatenate([M, T], 1).astype(np.uint8); n = M.shape[1]; r = 0; piv = []
    for c in range(n):
        rows = np.nonzero(A[r:, c])[0]
        if len(rows) == 0: continue
        p = rows[0] + r
        if p != r: A[[r, p]] = A[[p, r]]
        sel = np.nonzero(A[:, c])[0]; sel = sel[sel != r]; A[sel] ^= A[r]; piv.append(c); r += 1
    ok = ~A[r:, n:].any(0)
    C = np.zeros((n, T.shape[1]), np.uint8)
    for j, c in enumerate(piv): C[c] = A[j, n:]
    return ok, C
total = 0
for s in stops:
    Q, depth = snaps[s]
    live = [w for w in range(nq) if Q[w].any()]
    M = np.concatenate([np.ones((N, 1), bool), Q[live].T], 1)
    pairs = [(i, j) for i in range(len(live)) for j in range(i + 1, len(live))]
    T = np.stack([Q[live[i]] & Q[live[j]] for i, j in pairs], 1)
    ok, C = gf2_solve_all(M, T)
    hits = []
    for pi in np.nonzero(ok)[0]:
        i, j = pairs[pi]; coef = C[1:, pi]
        ws = [live[t] for t in np.nonzero(coef)[0] if t not in (i, j)]
        if ws and T[:, pi].any(): hits.append((live[i], live[j], ws))
    win = [tuple(map(int, w)) for w in W if w[0] <= s < w[1]]
    print(s, 'win', win[0] if win else None, 'live', len(live), 'cond-depth', depth, 'hits', len(hits), hits[:6], flush=True)
    total += len(hits)
print('total hits', total)
