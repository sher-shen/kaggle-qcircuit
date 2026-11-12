# Supervisor 2026-11-12 01:xx UTC. Generic per-case permutation extraction for a pure CSWAP window [A,B):
# every op must be a CSWAP (control in CTL, targets outside CTL) or a CX between CTL wires (free, linear control forms).
# Case = values of the CTL wires at A (bit i = CTL[i]). Per case the window is a fixed permutation of the data wires.
# Class of a data wire at A in a case: 'z'/'o' if constant over all x (and REPS outcome draws) in that case, else token d<w>.
# Writes the SA input (cswap_win_sa.c format) and a JSON with wires/forms for the builder.
# Usage: python3.13 cswap_win_extract.py ops.json A B CTL(comma) out_prefix [reps]
import json, sys, numpy as np
from simto import sim
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
A, B = int(sys.argv[2]), int(sys.argv[3]); CTL = [int(c) for c in sys.argv[4].split(',')]; out = sys.argv[5]
reps = int(sys.argv[6]) if len(sys.argv) > 6 else 1
mask = {c: 1 << i for i, c in enumerate(CTL)}; data = set(); orig_cnt = 0
for i in range(A, B):
    o = ops[i]; k = K[o[0]]
    assert o[-1] == -1, (i, k)
    if k == 'CSWAP': assert o[1] in mask and o[2] not in mask and o[3] not in mask; data |= {o[2], o[3]}; orig_cnt += 1
    elif k == 'CX': assert o[1] in mask and o[2] in mask
    else: raise SystemExit(f'op {i} {k} not allowed')
data = sorted(data); W = len(data); wi = {w: j for j, w in enumerate(data)}
xs = np.arange(1, 3133453, dtype=np.int64)  # verifier domain x>=1
const = {}  # case -> per wire: set of seen values
for r in range(reps):
    q, _ = sim(d, xs, A, 1000 + r)
    case = np.zeros(len(xs), np.int64)
    for c in CTL: case |= q[c].astype(np.int64) * mask[c]
    for cs in np.unique(case):
        sel = case == cs; e = const.setdefault(int(cs), [set() for _ in data])
        for j, w in enumerate(data): e[j] |= set(np.unique(q[w][sel]).tolist())
    cnt = {int(c): int(n) for c, n in zip(*np.unique(case, return_counts=True))}
cases = []
for cs, e in sorted(const.items()):
    start = ['z' if s == {0} else 'o' if s == {1} else f'd{data[j]}' for j, s in enumerate(e)]
    cur = list(start); m = dict(mask)
    for i in range(A, B):
        o = ops[i]; k = K[o[0]]
        if k == 'CX': m[o[2]] ^= m[o[1]]
        elif bin(m[o[1]] & cs).count('1') & 1:
            a, b = wi[o[2]], wi[o[3]]; cur[a], cur[b] = cur[b], cur[a]
    moved = sum(s != t for s, t in zip(start, cur))
    print('case', cs, 'x', cnt.get(cs), 'moved', moved)
    if moved or cs: cases.append({'case': cs, 'start': start, 'end': cur})
cases = [c for c in cases if c['start'] != c['end'] or c['case'] != 0]
toks = {}
with open(out + '.txt', 'w') as f:
    f.write(f'{W} {len(CTL)} {len(cases)}\n')
    for C in cases:
        f.write(str(C['case']) + ' ' + ' '.join(str(toks.setdefault(t, len(toks))) for t in C['start'] + C['end']) + '\n')
json.dump({'A': A, 'B': B, 'CTL': CTL, 'data': data, 'orig_cswaps': orig_cnt, 'cases': cases}, open(out + '.json', 'w'))
print('W', W, 'ncases', len(cases), 'orig CSWAPs', orig_cnt)
