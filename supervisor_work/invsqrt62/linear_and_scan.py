"""WARNING: one shot per x -> false positives (see README). For every Toffoli-class gate, test whether its product (a AND b for CCX, a AND b AND c for CCZ, the
swap condition for CSWAP) is an affine GF(2) function of the other live wires at that point, on a sample of x.
If so the gate could be replaced by CNOT/CZ (Clifford) logic, saving a Toffoli. Sample hits must be re-checked
on all x. Usage: python linear_and_scan.py ops.json [nsample]
"""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2
rng = np.random.default_rng(11)
xs = np.unique(np.concatenate([np.arange(1, 2049), rng.integers(1, MAXX + 1, ns)])).astype(np.int64); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
ONES = toint(np.ones(N, bool))
def in_span(vecs, t):
    basis = {}  # pivot bit -> vec
    for v in vecs:
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; break
    while t:
        p = t.bit_length() - 1
        if p in basis: t ^= basis[p]
        else: return False
    return True
hits = []
for i, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k in ('CCX', 'CCZ', 'CSWAP') and m.any():
        if k == 'CCX': prod = q[a[0]] & q[a[1]]; excl = {a[2]}
        elif k == 'CCZ': prod = q[a[0]] & q[a[1]] & q[a[2]]; excl = set()
        else: prod = q[a[0]] & (q[a[1]] != q[a[2]]); excl = set()
        sel = m  # only the executed shots matter
        vecs = [toint(q[j] & sel) for j in range(nq) if j not in excl and (q[j] & sel).any()] + [toint(sel)]
        if in_span(vecs, toint(prod & sel)):
            hits.append((i, k, a[:3], float(m.mean()))); print('HIT', i, k, a[:3], 'exec frac', m.mean(), flush=True)
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
print('hits', len(hits), 'sum exec frac', sum(h[3] for h in hits))
