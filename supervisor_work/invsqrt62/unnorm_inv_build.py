# Supervisor 2026-11-12 07:xx UTC. Rebuild the unnormalize CSWAP ladder as the literal inverse of the normalize segment.
# Fact (unnorm_inv_check): the state at unnormalize ladder start equals the state after normalize op 247 under the wire map
# MAP below, and the ladder end equals the state at normalize op 144 under the same map, controls identical.  So the ladder
# can be replaced by relabel(reverse(normalize ops 144..247)), with the wire-22 measurement trick (forward: free) undone by
# one explicit CCX into a clean ancilla.  The original ladder's wire-60 block (it also erases the decoder's wire 60) is
# replaced by a measured erase of wire 60 whose phase fix-up is solved exactly (affine / quadratic) on samples.
# Usage: python3.13 unnorm_inv_build.py p62m5.json out.json [A] -- indices are p62m5 indices.
import json, sys, numpy as np
from simto import sim
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
NS, NE = 144, 248            # normalize segment [NS, NE)
US, UE = 46816, 46892        # unnormalize region replaced
MAP = {i: i for i in range(14)}
MAP.update({14: 57, 15: 50, 16: 27, 17: 61, 18: 51, 19: 28, 20: 40, 21: 41, 42: 16, 43: 14, 44: 18, 45: 15, 46: 19})
A = int(sys.argv[3]) if len(sys.argv) > 3 else 22
MAP[22] = A
for i in range(US, UE):
    o = ops[i]; assert A not in o[1:-1] or K[o[0]] in ('HMR',) and False, (i, K[o[0]], o)
seg = ops[NS:NE]
# trick ops: HMR 22 (171) and the two conditioned CZ (172,173)
new = [['CX', 41, 19, -1]]
for j in range(NE - 1, NS - 1, -1):
    o = ops[j]; k = K[o[0]]; a = o[1:]
    if k == 'HMR':
        assert a[0] == 22
        # value of 22 just before the HMR is w44 & (w13 ^ w21) (checked below) -> recompute it
        new += [['CX', MAP[13], MAP[21], -1], ['CCX', MAP[44], MAP[21], A, -1], ['CX', MAP[13], MAP[21], -1]]
        continue
    if k == 'CZ': assert a[-1] >= 0; continue   # measurement-conditioned fix-ups of the forward trick
    assert a[-1] == -1, (j, k, a)
    if k == 'CX': new.append(['CX', MAP[a[0]], MAP[a[1]], -1])
    elif k == 'CSWAP': new.append(['CSWAP', MAP[a[0]], MAP[a[1]], MAP[a[2]], -1])
    elif k == 'X': new.append(['X', MAP[a[0]], -1])
    else: raise SystemExit((j, k))
# drop the reverse of op 247's partner? op 247 = CX 46->21 -> CX 19->41 ; together with the leading CX 41->19 it is the original 46816/46817
print('new ladder ops', len(new), 'CSWAP', sum(o[0] == 'CSWAP' for o in new), 'CCX', sum(o[0] == 'CCX' for o in new))
# check the trick formula on the forward circuit
rng = np.random.default_rng(5)
xs = np.unique(np.concatenate([np.arange(1, 8192), rng.integers(1, 3133453, 60000)])).astype(np.int64)
q, _ = sim(d, xs, 171, 3)
assert np.array_equal(q[22], q[44] & (q[13] ^ q[21])), 'trick formula'
print('trick formula w22 = w44 & (w13^w21) holds on', len(xs), 'x')
# state at end of new ladder: simulate original up to US, then apply 'new' manually via a temp circuit
d2 = dict(d); d2['ops'] = ops[:US] + [[KI[o[0]]] + o[1:] for o in new]
q2, _ = sim(d2, xs, len(d2['ops']), 3)
q1, _ = sim(d, xs, UE, 3)  # original after the region
diff = [w for w in range(d['n_qubits']) if not np.array_equal(q1[w], q2[w])]
print('wires differing from original after region:', diff, 'ancilla A clean:', not q2[A].any())
json.dump({'new': new, 'diff': diff}, open(sys.argv[2], 'w'))
