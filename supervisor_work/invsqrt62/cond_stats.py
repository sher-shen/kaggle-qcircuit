"""Per classically-conditioned block (PUSH_CONDITION ... POP_CONDITION, outermost level) and per
classically-conditioned Toffoli-class gate: execution probability and mean Toffolis contributed.
Every x is repeated R times with fresh HMR outcomes (one shot per x gives wrong statistics here).
Also: Toffolis by stage if a stages.json (list of [name, start_op, end_op]) is given.
Usage: python cond_stats.py ops.json [nx_sample] [R] [stages.json]
"""
import json, sys
import numpy as np
from collections import defaultdict
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
R = int(sys.argv[3]) if len(sys.argv) > 3 else 16
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2
rng = np.random.default_rng(5)
xs0 = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs0, R); N = len(xs)
# weight so that the sample approximates the uniform average over x in [1, MAXX]
w = np.where(xs <= 1024, 1.0, 0.0); nsmall = 1024; nbig = len(xs0) - 1024
w = np.where(xs <= 1024, (nsmall / MAXX) / (nsmall * R), ((MAXX - nsmall) / MAXX) / (max(nbig, 1) * R))
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
blk = []  # (start_op, end_op, prob, toffolis inside)
cur = None; tof_in = 0.0
gate_cond = defaultdict(float)  # op -> weighted exec for conditioned Toffoli-class gates outside blocks
total = 0.0
for i, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION':
        if not stack: cur = [i, None, float((w * (act & B(o[1]))).sum())]; tof_in = 0.0
        stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION':
        act = stack.pop()
        if not stack: cur[1] = i; blk.append((cur[0], cur[1], cur[2], tof_in))
        continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k in ('CCX', 'CCZ', 'CSWAP'):
        t = float((w * m).sum()); total += t
        if stack: tof_in += t
        elif cond >= 0: gate_cond[i] += t
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
print(f'mean Toffoli (weighted sample) {total:.2f}')
print(f'conditioned blocks: {len(blk)}, Toffolis inside {sum(b[3] for b in blk):.2f}; '
      f'conditioned single gates: {len(gate_cond)}, Toffolis {sum(gate_cond.values()):.2f}')
print('top blocks by Toffolis: start end prob tof tof/prob')
for b in sorted(blk, key=lambda b: -b[3])[:25]:
    print(f'  {b[0]:6d} {b[1]:6d} p={b[2]:.3f} tof={b[3]:.3f} static~{b[3] / max(b[2], 1e-9):.1f}')
if len(sys.argv) > 4:
    st = json.load(open(sys.argv[4]))
    print('stages json present; map blocks to stages yourself with the start op')
