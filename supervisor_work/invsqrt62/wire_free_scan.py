"""Instruction 3 of 05:25 (free a wire non-linearly around a width-62 dirty block), supervisor 2026-11-08 06 UTC.
For op window [P,Q): every live wire w not touched inside the window is tested for  w = g*h + r  with g, h, r affine in the
other live wires and the measurement bits of the last 400 ops (at P and, separately, at Q), g = one live wire or XOR of two (+const).  Such a w could be HMR-erased before
P (phase fix-up CZ(g,h) Z(r) = Clifford) and recomputed after Q with ONE Toffoli, giving a clean ancilla inside the window.
Usage: wire_free_scan.py ops.json P Q [nsample] [reps] [extra]"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); P, Qe = int(sys.argv[2]), int(sys.argv[3])
ns = int(sys.argv[4]) if len(sys.argv) > 4 else 1500; REPS = int(sys.argv[5]) if len(sys.argv) > 5 else 4
EXTRA = int(sys.argv[6]) if len(sys.argv) > 6 else 2
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(19)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
def in_span(vecs, f):
    basis = {}
    for v in vecs:
        v = toint(v)
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; break
    t = toint(f)
    while t:
        p = t.bit_length() - 1
        if p in basis: t ^= basis[p]
        else: return False
    return True
QA = {'CX': 2, 'CCX': 3, 'CSWAP': 3, 'SWAP': 2, 'X': 1, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'HMR': 1, 'R': 1, 'Z_POW': 1, 'S': 1, 'T': 1}
touched = set()
for i in range(P, Qe):
    k = K[ops[i][0]]
    if k in QA: touched.update(ops[i][1:1 + QA[k]])
snaps = {}; bsn = {}; bitt = {}
for idx, o in enumerate(ops):
    if idx in (P, Qe): snaps[idx] = q.copy(); bsn[idx] = [B(b).copy() for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
    if idx >= Qe: break
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
        r = rng.random(N) < 0.5; bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m; bitt[a[1]] = idx
    elif k == 'R': q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE0': B(a[0])[m] = False
    elif k == 'BIT_STORE1': B(a[0])[m] = True
SP, SQ = snaps[P], snaps[Qe]
liveP = [w for w in range(nq) if SP[w].any()]
print('live at P', len(liveP), 'untouched live', [w for w in liveP if w not in touched], flush=True)
for w in liveP:
    if w in touched: continue
    res = []
    for S, bs in ((SP, bsn[P]), (SQ, bsn[Qe])):
        others = [u for u in range(nq) if u != w and S[u].any()]
        V = np.array([np.ones(N, bool)] + [S[u] for u in others] + bs); f = S[w]
        if in_span(V, f): res.append('affine'); continue
        found = None
        for e in range(1, EXTRA + 1):
            for combo in itertools.combinations(range(len(others)), e):
                g = np.zeros(N, bool)
                for c in combo: g ^= S[others[c]]
                if not g.any() or g.all(): continue
                if in_span(V[:, ~g], f[~g]) and in_span(V[:, g], f[g]): found = [others[c] for c in combo]; break
            if found is not None: break
        res.append(found)
    print('wire', w, 'P:', res[0], 'Q:', res[1], flush=True)
