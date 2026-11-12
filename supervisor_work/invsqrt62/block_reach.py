"""Reachable entry patterns of each block (block_extract.py output) over all x (stride option), simulating the
circuit like live_trace.py (HMR outcomes random, seed arg).  Adds 'reach': sorted list of W-patterns seen at the
block's first op while its condition context is active.  Usage: block_reach.py ops.json blocks.json out.json [stride seed]"""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); blocks = json.load(open(sys.argv[2])); out = sys.argv[3]
stride = int(sys.argv[4]) if len(sys.argv) > 4 else 1; seed = int(sys.argv[5]) if len(sys.argv) > 5 else 7
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']; MAXX = 3 * (2**10 - 2)**2
QARGS = {'X': 1, 'CX': 2, 'CCX': 3, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'SWAP': 2, 'CSWAP': 3, 'R': 1, 'HMR': 1, 'Z_POW': 1}
at = {}
for bi, b in enumerate(blocks): at.setdefault(b['ops'][0], []).append(bi)
reach = [set() for _ in blocks]
rng = np.random.default_rng(seed); allx = np.arange(1, MAXX + 1, stride, dtype=np.int64); CH = 1 << 18
for s in range(0, len(allx), CH):
    xs = allx[s:s + CH]; N = len(xs); q = np.zeros((nq, N), bool)
    for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
    bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
    for i, o in enumerate(ops):
        k = K[o[0]]
        if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
        if k == 'POP_CONDITION': act = stack.pop(); continue
        if k not in QARGS:
            cond = o[-1]; m = act & B(cond) if cond >= 0 else act
            if k == 'BIT_INVERT': B(o[1])[m] ^= True
            elif k == 'BIT_STORE0': B(o[1])[m] = False
            elif k == 'BIT_STORE1': B(o[1])[m] = True
            continue
        cond = o[-2] if k == 'Z_POW' else o[-1]
        m = act & B(cond) if cond >= 0 else act
        a = o[1:1 + QARGS[k]]
        for bi in at.get(i, ()):
            code = np.zeros(N, np.int64)
            for p, w in enumerate(blocks[bi]['W']): code |= q[w].astype(np.int64) << p
            reach[bi].update(np.unique(code[m]).tolist())
        if k == 'X': q[a[0]] ^= m
        elif k == 'CX': q[a[1]] ^= m & q[a[0]]
        elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
        elif k == 'CSWAP':
            u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
        elif k == 'SWAP':
            u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
        elif k == 'HMR':
            r = rng.random(N) < 0.5; bb = B(o[2]); bb[m] = r[m]; q[a[0]] &= ~m
        elif k == 'R': q[a[0]] &= ~m
    print(s, file=sys.stderr, flush=True)
for b, r in zip(blocks, reach): b['reach'] = sorted(r)
json.dump(blocks, open(out, 'w'))
from collections import Counter
print(Counter((len(b['W']), len(b['reach'])) for b in blocks))
