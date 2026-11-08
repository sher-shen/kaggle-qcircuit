"""Find dirty-ancilla compute/uncompute pairs: two unconditioned CCX with formally identical operands (same affine masks)
onto the same target wire, i.e. t ^= ab ... t ^= ab with t not clean. If a clean wire is free over the whole span
(occupancy < 62 from live_trace), the product could live in a clean ancilla and the second CCX becomes an HMR uncompute.
Usage: dirty_pairs.py ops.json live.npz [maxgap]"""
import json, sys, numpy as np
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
z = np.load(sys.argv[2]); live = z['live']; before = z['before']; maxgap = int(sys.argv[3]) if len(sys.argv) > 3 else 60
QARGS = {'X': 1, 'CX': 2, 'CCX': 3, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'SWAP': 2, 'CSWAP': 3, 'R': 1, 'HMR': 1, 'Z_POW': 1}
cur = np.zeros(nq, bool); cur[d['x_qubits']] = True; occ = np.zeros(len(ops), int)
for i, o in enumerate(ops):
    k = K[o[0]]
    if k not in QARGS: occ[i] = cur.sum(); continue
    a = o[1:1 + QARGS[k]]; du = cur.copy()
    for j, qq in enumerate(a): du[qq] |= before[i, j] | live[i, j]
    occ[i] = du.sum()
    for j, qq in enumerate(a): cur[qq] = live[i, j]
W = [(1 << w, 0) for w in range(nq)]; nf = [0]
def fresh(): nf[0] += 1; return (1 << (nq + nf[0]), 0)
cond = 0; last = {}  # (maskpair, target) -> op index
hits = []
for i, o in enumerate(ops):
    k = K[o[0]]; a = o[1:]
    if k == 'PUSH_CONDITION': cond += 1; continue
    if k == 'POP_CONDITION': cond -= 1; continue
    if k in ('NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'Z', 'CZ', 'CCZ', 'Z_POW'): continue
    cnd = cond or (k in QARGS and a[QARGS[k] - (0 if k != 'Z_POW' else 0)] >= 0 if k not in ('Z_POW',) else False)
    if k == 'X': W[a[0]] = (W[a[0]][0], W[a[0]][1] ^ 1) if not cnd else fresh()
    elif k == 'CX': W[a[1]] = (W[a[1]][0] ^ W[a[0]][0], W[a[1]][1] ^ W[a[0]][1]) if not cnd else fresh()
    elif k == 'SWAP':
        if cnd: W[a[0]] = fresh(); W[a[1]] = fresh()
        else: W[a[0]], W[a[1]] = W[a[1]], W[a[0]]
    elif k in ('HMR', 'R'): W[a[0]] = (0, 0)
    elif k == 'CSWAP': W[a[1]] = fresh(); W[a[2]] = fresh()
    elif k == 'CCX':
        if cnd: W[a[2]] = fresh(); continue
        key = (frozenset([W[a[0]], W[a[1]]]), a[2])
        if key in last and i - last[key] <= maxgap:
            j = last[key]; hits.append((j, i, a[2], int(occ[j:i + 1].max())))
            del last[key]
        else: last[key] = i
        W[a[2]] = fresh()
print('pairs', len(hits)); print('with clean wire available (maxocc<62):', [h for h in hits if h[3] < 62])
print('all (first 40):', hits[:40])
