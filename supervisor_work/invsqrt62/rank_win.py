import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); W = np.load(sys.argv[2]); probe=set()
for a,b in W: probe.update([int(a), int((a+b)//2), int(b-1)])
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2
rng = np.random.default_rng(3)
xs = np.unique(np.concatenate([np.arange(1, 4097), rng.integers(1, MAXX + 1, 6000)])).astype(np.int64)
N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
def gf2rank(M):
    M = M.copy().astype(np.uint8); r = 0; rows, cols = M.shape
    for c in range(cols):
        p = np.nonzero(M[r:, c])[0]
        if len(p) == 0: continue
        p = p[0] + r; M[[r, p]] = M[[p, r]]
        nz = np.nonzero(M[:, c])[0]; nz = nz[nz != r]; M[nz] ^= M[r]
        r += 1
        if r == rows: break
    return r
res = []
for i, o in enumerate(ops):
    if i in probe:
        live = q.any(1); L = q[live]
        A = np.vstack([L, np.ones((1, N), bool)])  # affine
        rk = gf2rank(A.T.T) if False else gf2rank(A)
        
        print(i, live.sum(), 'affine rank', rk - 1, flush=True)
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP':
        u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
    elif k == 'SWAP':
        u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
    elif k == 'HMR':
        r = rng.random(N) < 0.5; bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m
    elif k == 'R': q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE0': B(a[0])[m] = False
    elif k == 'BIT_STORE1': B(a[0])[m] = True
