# Supervisor 2026-11-12. Find mirrored segment pairs: checkpoints p<p'<q'<q with state(p) ~ state(q) and state(p') ~ state(q')
# (state = multiset of non-zero wire value vectors over sample x, i.e. equal up to a wire relabel). Then [q',q) could be replaced
# by the inverse of [p,p') (or vice versa); report the static Toffoli counts of both halves.
# Usage: python3.13 mirror_scan.py ops.json [step] [nx]
import json, sys, hashlib, numpy as np
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
step = int(sys.argv[2]) if len(sys.argv) > 2 else 8; nx = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
rng = np.random.default_rng(2); xs = np.unique(np.concatenate([np.arange(1, 1024), rng.integers(1, 3133453, nx)])).astype(np.int64)
N = len(xs); nq = d['n_qubits']; q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool); r2 = np.random.default_rng(3)
TOF = {'CCX', 'CCZ', 'CSWAP'}; tofc = [0]; cps = []; depth = []
def sig():
    hs = sorted(hashlib.md5(np.packbits(q[w]).tobytes()).hexdigest()[:12] for w in range(nq) if q[w].any())
    return hash(tuple(hs))
for i, o in enumerate(ops):
    if i % step == 0: cps.append((i, sig(), tofc[0], len(stack)))
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]; m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k in TOF: tofc[0] += 1
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP': u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
    elif k == 'SWAP': u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
    elif k in ('HMR', 'R'):
        rr = r2.random(N) < 0.5
        if k == 'HMR': bb = B(a[1]); bb[m] = rr[m]
        q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE1': B(a[0])[m] = True
cps.append((len(ops), sig(), tofc[0], 0))
by = {}
for idx, (i, s, t, dep) in enumerate(cps): by.setdefault(s, []).append(idx)
pairs = [(a, b) for v in by.values() for x, a in enumerate(v) for b in v[x + 1:] if cps[b][0] - cps[a][0] > step]
print('checkpoints', len(cps), 'equal-state pairs', len(pairs))
ps = set(pairs); res = []
for (a, b) in pairs:
    for (a2, b2) in pairs:
        if a < a2 < b2 < b and (a, b) != (a2, b2):
            F = cps[a2][2] - cps[a][2]; Bk = cps[b][2] - cps[b2][2]
            if F != Bk and min(F, Bk) >= 0 and abs(F - Bk) >= 1:
                res.append((abs(F - Bk), cps[a][0], cps[a2][0], cps[b2][0], cps[b][0], F, Bk))
res.sort(reverse=True)
seen = set()
for r in res[:60]:
    print('diff %d  fwd [%d,%d) tof %d   bwd [%d,%d) tof %d' % (r[0], r[1], r[2], r[5], r[3], r[4], r[6]))
