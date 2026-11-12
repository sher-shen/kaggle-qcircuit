# Supervisor 2026-11-12 04:xx UTC. Extended normalize window incl. wire 22 (the "wire-22 trick") for the transvection model.
# Region [A,E) of a p62m5-layout ops.json: CSWAPs (control in CTL), CX among CTL (free form changes), CX among data wires
# (free unconditional transvections, f = 0), one HMR on wire 22 (marker MU, wire 22 measured in X basis, then 0) and the
# outcome-conditioned CZ fix-ups right after it (phase only, skipped).  Per case (CTL values at A) everything is affine in the
# start tokens.  Writes: out.txt  "W NCT NC" then per case: cm, start[W], end[W], z (value of 22 at MU)  (affine masks, bit W = 1)
#                        out_gates.txt  the original region as "0xL 0xv f" lines (f = 0: free CX) with a line "MU" at the HMR.
# Usage: python3.13 ext22.py ops.json A E CTL(comma) out_prefix [reps]
import json, sys, numpy as np
from simto import sim
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
A, E = int(sys.argv[2]), int(sys.argv[3]); CTL = [int(c) for c in sys.argv[4].split(',')]; out = sys.argv[5]
reps = int(sys.argv[6]) if len(sys.argv) > 6 else 1
mask = {c: 1 << i for i, c in enumerate(CTL)}; data = set(); gates = []; m = dict(mask); hmr = None
for i in range(A, E):
    o = ops[i]; k = K[o[0]]
    if k == 'CSWAP': assert o[1] in mask and o[-1] == -1; data |= {o[2], o[3]}
    elif k == 'CX':
        assert o[-1] == -1
        if o[1] in mask: assert o[2] in mask
        else: assert o[2] not in mask; data |= {o[1], o[2]}
    elif k == 'HMR': assert hmr is None; hmr = i; data.add(o[1])
    elif k == 'CZ': assert o[-1] >= 0 and hmr is not None
    else: raise SystemExit(f'op {i} {k} not allowed')
data = sorted(data); W = len(data); wi = {w: j for j, w in enumerate(data)}
for i in range(A, E):
    o = ops[i]; k = K[o[0]]
    if k == 'CSWAP': b = (1 << wi[o[2]]) | (1 << wi[o[3]]); gates.append((b, b, m[o[1]]))
    elif k == 'CX' and o[1] in mask: m[o[2]] ^= m[o[1]]
    elif k == 'CX': gates.append((1 << wi[o[1]], 1 << wi[o[2]], 0))
    elif k == 'HMR': gates.append('MU')
xs = np.arange(1, 3133453, dtype=np.int64); const = {}; cnt = {}
for r in range(reps):
    q, _ = sim(d, xs, A, 1000 + r)
    case = np.zeros(len(xs), np.int64)
    for c in CTL: case |= q[c].astype(np.int64) * mask[c]
    for cs in np.unique(case):
        sel = case == cs; e = const.setdefault(int(cs), [set() for _ in data])
        for j, w in enumerate(data): e[j] |= set(np.unique(q[w][sel]).tolist())
    cnt = {int(c): int(n) for c, n in zip(*np.unique(case, return_counts=True))}
par = lambda x: bin(x).count('1') & 1
def ap(s, g, cs):
    L, v, f = g
    if f and not par(f & cs): return s
    a = 0
    for w in range(W):
        if L >> w & 1: a ^= s[w]
    return [s[w] ^ (a if v >> w & 1 else 0) for w in range(W)] if a else s
lines = []; i22 = wi[22] if 22 in wi else None
for cs, e in sorted(const.items()):
    start = [0 if s == {0} else (1 << W) if s == {1} else 1 << j for j, s in enumerate(e)]
    s = list(start); z = None
    for g in gates:
        if g == 'MU': z = s[i22]; s[i22] = 0; continue
        s = ap(s, g, cs)
    lines.append((cs, start, s, z))
    print('case', cs, 'x', cnt.get(cs), 'moved', sum(a != b for a, b in zip(start, s)), 'z', hex(z))
with open(out + '.txt', 'w') as f:
    f.write(f'{W} {len(CTL)} {len(lines)}\n')
    for cs, st, en, z in lines: f.write(' '.join(map(str, [cs] + st + en + [z])) + '\n')
with open(out + '_gates.txt', 'w') as f:
    for g in gates: f.write('MU\n' if g == 'MU' else f'{hex(g[0])} {hex(g[1])} {g[2]}\n')
json.dump({'A': A, 'E': E, 'CTL': CTL, 'data': data, 'hmr': hmr}, open(out + '.json', 'w'))
print('W', W, 'data', data, 'ncases', len(lines), 'gates', sum(1 for g in gates if g != 'MU' and g[2]), 'free', sum(1 for g in gates if g != 'MU' and not g[2]))
