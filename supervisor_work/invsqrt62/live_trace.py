"""Exact qubit-liveness trace of an ops.json circuit over all x in [1, max_x] (or a stride sample).

For every op i and every qubit argument j, records whether that qubit is nonzero for ANY x after op i.
Since the circuit has no Hadamards outside HMR (which leaves the qubit |0>), a qubit that is 0 for every x
is genuinely |0> and can be reused. Prints the peak number of simultaneously-live qubits and where it occurs.
Usage: python live_trace.py ops.json out.npz [stride]
"""
import json, sys
import numpy as np

d = json.load(open(sys.argv[1])); out = sys.argv[2]
stride = int(sys.argv[3]) if len(sys.argv) > 3 else 1
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2
QARGS = {'X': 1, 'CX': 2, 'CCX': 3, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'SWAP': 2, 'CSWAP': 3, 'R': 1, 'HMR': 1, 'Z_POW': 1}
# live[i, j] = qubit arg j of op i nonzero for some x after op i ; before[i, j] likewise before op i
live = np.zeros((len(ops), 3), bool); before = np.zeros((len(ops), 3), bool)
rng = np.random.default_rng(7)
allx = np.arange(1, MAXX + 1, stride, dtype=np.int64)
CH = 1 << 18
for s in range(0, len(allx), CH):
    xs = allx[s:s + CH]; N = len(xs)
    q = np.zeros((nq, N), bool)
    for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
    bits = {}
    B = lambda i: bits.setdefault(i, np.zeros(N, bool))
    stack = []; act = np.ones(N, bool)
    for i, o in enumerate(ops):
        k = K[o[0]]
        if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
        if k == 'POP_CONDITION': act = stack.pop(); continue
        if k not in QARGS:
            cond = o[-1]; m = act & B(cond) if cond >= 0 else act
            if k == 'BIT_INVERT': B(o[1])[m] ^= True
            elif k == 'BIT_STORE0': B(o[1])[m] = False
            elif k == 'BIT_STORE1': B(o[1])[m] = True
            elif k != 'NEG': raise ValueError(k)
            continue
        cond = o[-2] if k == 'Z_POW' else o[-1]
        m = act & B(cond) if cond >= 0 else act
        a = o[1:1 + QARGS[k]]
        for j, qq in enumerate(a): before[i, j] |= q[qq].any()
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
        for j, qq in enumerate(a): live[i, j] |= q[qq].any()
    print(s, file=sys.stderr, flush=True)
np.savez_compressed(out, live=live, before=before)
# occupancy per op
cur = np.zeros(nq, bool); cur[d['x_qubits']] = True
occ = np.zeros(len(ops), np.int32)
for i, o in enumerate(ops):
    k = K[o[0]]
    if k not in QARGS: occ[i] = cur.sum(); continue
    a = o[1:1 + QARGS[k]]
    during = cur.copy()
    for j, qq in enumerate(a): during[qq] |= before[i, j] | live[i, j]
    occ[i] = during.sum()
    for j, qq in enumerate(a): cur[qq] = live[i, j]
print('peak occupancy', occ.max(), 'ops at peak', int((occ == occ.max()).sum()), 'first/last', int(np.argmax(occ == occ.max())), int(len(occ) - 1 - np.argmax((occ == occ.max())[::-1])))
print('ops with occ>=61', int((occ >= 61).sum()), ' >=60', int((occ >= 60).sum()))
np.save(out.replace('.npz', '_occ.npy'), occ)
