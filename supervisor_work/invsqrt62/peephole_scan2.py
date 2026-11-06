"""Basis-state trace of an ops.json circuit over many inputs x (random HMR outcomes) to find
Toffoli-class gates that are reducible on every execution:
  CCX/CCZ with a control constant 0 (drop) or constant 1 (-> CX/CZ), controls equal (-> CX/CZ) or complementary (drop);
  CSWAP with control constant 0 (drop) / 1 (-> SWAP) or both targets equal (drop).
Also (v2): CSWAP targets complementary when control=1 (-> 2 CX) and one target 0 (info only).
Usage: python peephole_scan2.py ops.json [n_samples] [seed]
"""
import json, sys
import numpy as np

d = json.load(open(sys.argv[1]))
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 20
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
MAXX = 3 * (2**10 - 2)**2
xs = np.concatenate([np.arange(1, 4097), rng.integers(1, MAXX + 1, N - 4096)]).astype(np.int64)
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}
B = lambda i: bits.setdefault(i, np.zeros(N, bool))
stack = []; act = np.ones(N, bool)
findings = []
for i, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION':
        stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION':
        act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act
    if not m.any():
        if k in ('CCX', 'CCZ', 'CSWAP'): findings.append((i, k, 'never runs'))
        continue
    a = o[1:]
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k in ('CCX', 'CCZ'):
        c1, c2 = q[a[0]][m], q[a[1]][m]
        tag = None
        if not c1.any() or not c2.any(): tag = 'control const 0 -> drop'
        elif c1.all(): tag = 'c1 const 1 -> C' + k[2:]
        elif c2.all(): tag = 'c2 const 1 -> C' + k[2:]
        elif (c1 == c2).all(): tag = 'controls equal -> C' + k[2:]
        elif (c1 != c2).all(): tag = 'controls complementary -> drop'
        if k == 'CCZ':
            t = q[a[2]][m]
            if not t.any(): tag = tag or 'target const 0 -> drop'
            elif t.all(): tag = tag or 'target const 1 -> CZ'
        if tag: findings.append((i, k, tag, float(m.mean())))
        if k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP':
        c, u, v = q[a[0]], q[a[1]], q[a[2]]
        cm, um, vm = c[m], u[m], v[m]
        tag = None
        if not cm.any(): tag = 'control const 0 -> drop'
        elif cm.all(): tag = 'control const 1 -> SWAP'
        elif (um[cm] == vm[cm]).all(): tag = 'targets equal when control=1 -> drop'
        elif (um[cm] != vm[cm]).all(): tag = 'targets complementary when control=1 -> CX c u; CX c v'
        elif (~um[cm]).all() or (~vm[cm]).all(): tag = 'one target 0 when control=1'
        if tag: findings.append((i, k, tag, float(m.mean())))
        s = m & c & (u != v); q[a[1]] ^= s; q[a[2]] ^= s
    elif k == 'SWAP':
        u, v = q[a[0]], q[a[1]]; s = m & (u != v); u ^= s; v ^= s
    elif k == 'HMR':
        r = rng.random(N) < 0.5
        bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m
    elif k == 'R': q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE0': B(a[0])[m] = False
    elif k == 'BIT_STORE1': B(a[0])[m] = True
    # Z, CZ, NEG, Z_POW: phase only
print('qubits clean at end:', not q[[i for i in range(nq) if i not in d['x_qubits']]].any(),
      'x restored:', all(((xs >> k) & 1 == q[qq]).all() for k, qq in enumerate(d['x_qubits'])))
for f in findings: print(*f)
print(len(findings), 'findings')
