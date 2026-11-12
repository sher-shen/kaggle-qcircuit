# Supervisor 2026-11-12 03:xx UTC. Builder for cswap_win_tv.c solutions (transvection model): replace the pure window [A,B)
# of ops.json by the network. Gate (L, v, f): x -> x ^ f*<L,x>*v with popcount(L&v) even, realised as
# CX network A (y = A x with L A^-1 = e_a*, A v = e_b), CCX(ctl, a -> b), CX network A^-1. Gates with L = v = {a,b} become a plain CSWAP.
# Control forms: free CX among CTL wires (BFS, as in cswap_win_build.py); CTL restored to the original end forms.
# Self-check: the region's data-wire action is simulated on random bit vectors for every gate.
# Usage: python3 tv_build.py ops.json win.json tv.log out.json
import json, sys, re, itertools, random
from collections import deque
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
w = json.load(open(sys.argv[2])); A, B, CTL, data = w['A'], w['B'], w['CTL'], w['data']; W = len(data)
gates = [(int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))) for l in open(sys.argv[3])
         for m in [re.match(r'tv \d+ 0x([0-9a-f]+) 0x([0-9a-f]+) (\d+)', l)] if m]
n = len(CTL); m = {c: 1 << i for i, c in enumerate(CTL)}
for i in range(A, B):
    o = ops[i]
    if K[o[0]] == 'CX': m[o[2]] ^= m[o[1]]
endst = tuple(m[c] for c in CTL)
def bfs(start, goal):
    Q = deque([(start, [])]); seen = {start}
    while Q:
        s, p = Q.popleft()
        if goal(s): return s, p
        for i, j in itertools.permutations(range(n), 2):
            t = list(s); t[j] ^= t[i]; t = tuple(t)
            if t not in seen: seen.add(t); Q.append((t, p + [[KI['CX'], CTL[i], CTL[j], -1]]))
bits = lambda x: [i for i in range(W) if x >> i & 1]
def rank(vs):
    r = []; 
    for x in vs:
        for p in r: x = min(x, x ^ p)
        if x: r.append(x)
    return len(r)
def cx_synth(cols):
    # cols: columns of M (ints over W bits); returns CX list (i, j) meaning x_j ^= x_i that maps state x -> M^-1 x ... built via
    # Gaussian elimination of M to I with row ops; row op 'row j ^= row i' on M == CX(i->j) applied to the vector M x.
    rows = [sum(((cols[c] >> r) & 1) << c for c in range(W)) for r in range(W)]; seq = []
    for c in range(W):
        if not rows[c] >> c & 1:
            r = next(r for r in range(c + 1, W) if rows[r] >> c & 1); rows[c] ^= rows[r]; seq.append((r, c))
        for r in range(W):
            if r != c and rows[r] >> c & 1: rows[r] ^= rows[c]; seq.append((c, r))
    return seq  # applying seq (in order) to y = M x gives x;  so applying it to x gives M^-1 x
def tv_ops(L, v):
    # find M with columns: M e_b = v, L(M e_j) = delta_ja.  Then A = M^-1: CX seq S maps x -> A x; reversed(S) maps back.
    a0 = bits(L)[0]; ker = [v]
    for j in range(W):
        e = 1 << j; e2 = e ^ (1 << a0) if (L >> j & 1) else e  # in ker L
        if e2 and rank(ker + [e2]) > len(ker): ker.append(e2)
    assert len(ker) == W - 1
    cols = [None] * W; aa, bb = 0, 1
    cols[aa] = 1 << a0; cols[bb] = v; rest = iter(ker[1:])
    for j in range(W):
        if cols[j] is None: cols[j] = next(rest)
    S = cx_synth(cols); return S, aa, bb
def apply_cx(x, seq):
    for i, j in seq:
        if x >> i & 1: x ^= 1 << j
    return x
st = tuple(1 << i for i in range(n)); new = []; rnd = random.Random(1)
for L, v, f in gates:
    st, p = bfs(st, lambda s: f in s); new += p; cw = CTL[st.index(f)]
    if L == v and bin(L).count('1') == 2:
        a, b = bits(L); new.append([KI['CSWAP'], cw, data[a], data[b], -1]); continue
    S, a, b = tv_ops(L, v)
    for _ in range(200):  # self-check of x -> x ^ <L,x> v
        x = rnd.getrandbits(W); y = apply_cx(x, S)
        if y >> a & 1: y ^= 1 << b
        y = apply_cx(y, S[::-1])
        assert y == x ^ (v if bin(L & x).count('1') & 1 else 0), (L, v)
    new += [[KI['CX'], data[i], data[j], -1] for i, j in S]
    new.append([KI['CCX'], cw, data[a], data[b], -1])
    new += [[KI['CX'], data[i], data[j], -1] for i, j in S[::-1]]
st, p = bfs(st, lambda s: s == endst); new += p
Z = d['zpow_exact']; assert all(int(k) < A or int(k) >= B for k in Z)
sh = len(new) - (B - A)
d['zpow_exact'] = {str(int(k) + (sh if int(k) >= B else 0)): v for k, v in Z.items()}
d['ops'] = ops[:A] + new + ops[B:]; d['n_ops'] = len(d['ops']); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[4], 'w'))
print('gates', len(gates), 'region ops', len(new), 'CSWAP', sum(K[o[0]] == 'CSWAP' for o in new), 'CCX', sum(K[o[0]] == 'CCX' for o in new))
