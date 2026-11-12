# Supervisor 2026-11-11 23:xx UTC. Extract the per-case permutation problem for normalize levels 44+45.
# Region (reordered, all moves are between disjoint-wire ops): trick 192-196 first, then the 21 CSWAPs
# 186-191,197-199,202-211,216,217 (controls via CX 200/201/212 on wires 43..45), then 213-215.
# Output: JSON with, per case (r43,r44,r45), the start/end class of wires 0..21: 'z','o' or data token id.
# Usage: python3.13 n4445_sat_extract.py p62mm.json cases.json
import json, sys, numpy as np
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
N = 3133453; X = np.arange(N, dtype=np.int64)
q = np.zeros((64, N), dtype=bool)
for j in range(22): q[j] = (X >> j) & 1
def ap(i):
    o = ops[i]; k = K[o[0]]
    if k == 'CSWAP':
        c, a, b = o[1], o[2], o[3]; m = q[c] & (q[a] ^ q[b]); q[a] ^= m; q[b] ^= m
    elif k == 'X': q[o[1]] ^= True
    elif k == 'CX': q[o[2]] ^= q[o[1]]
    elif k == 'CCX': q[o[3]] ^= q[o[1]] & q[o[2]]
    elif k in ('HMR', 'R'): q[o[1]] = False
    elif k in ('CZ', 'Z', 'CCZ'): pass
    else: raise SystemExit('unexpected ' + k + ' at %d' % i)
for i in range(186): ap(i)
for i in range(192, 197): ap(i)
r43 = q[43].copy(); r44 = q[44] ^ q[43]; r45 = q[45].copy()
start = q[:22].copy()
region = list(range(186, 192)) + [197, 198, 199, 200, 201] + list(range(202, 213)) + [216, 217]
# 216/217 are controlled by raw r45 after 212 restores it: apply in this order
for i in region: ap(i)
end = q[:22].copy()
# check against the original order
q2 = q
case = r43.astype(int) | (r44.astype(int) << 1) | (r45.astype(int) << 2)
out = []
for c in sorted(set(np.unique(case).tolist())):
    m = case == c; S = start[:, m]; E = end[:, m]
    def cls(v, toks):
        if not v.any(): return 'z'
        if v.all(): return 'o'
        for t, w in toks.items():
            if np.array_equal(v, w): return t
        return None
    toks = {}
    sc = []
    for w in range(22):
        v = S[w]
        if not v.any(): sc.append('z')
        elif v.all(): sc.append('o')
        else:
            dup = cls(v, toks)
            if dup is not None: raise SystemExit('duplicate data on wire %d case %d' % (w, c))
            toks['d%d' % w] = v; sc.append('d%d' % w)
    ec = []
    for w in range(22):
        t = cls(E[w], toks)
        if t is None: raise SystemExit('end wire %d case %d not a permutation' % (w, c))
        ec.append(t)
    assert sorted(sc) == sorted(ec), (c, sc, ec)
    out.append({'case': [c & 1, (c >> 1) & 1, (c >> 2) & 1], 'count': int(m.sum()), 'start': sc, 'end': ec})
    print(c & 1, (c >> 1) & 1, (c >> 2) & 1, int(m.sum()), 'moved', sum(a != b for a, b in zip(sc, ec)))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
