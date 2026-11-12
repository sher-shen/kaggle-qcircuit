# Supervisor 2026-11-12 04:xx UTC. Builder for tv22_sa.c solutions: replace region [A,E) (ext22.py) of ops.json by
#   gates[:MU] ; CTL -> raw case bits ; CX 22 -> S ; HMR 22 (bit HB) ; outcome-conditioned Z/CZ fix-ups ; gates[MU:] ; CTL -> end forms.
# Fix-ups: solve z_c = q0(c) ^ sum_w lam_w(c) s_c[w] exactly over GF(2) (lam_w affine, q0 quadratic in the case bits), then
#   lam_{w,0} -> Z(w), lam_{w,i} -> CZ(CTL[i-1], w), q0 b_i -> Z(CTL[i-1]), q0 b_i b_j -> CZ(CTL[i-1], CTL[j-1])  (all conditioned on HB).
# Gates are realised as in tv_build.py (CSWAP when L = v = {a,b}, else CX network + CCX + inverse network, self-checked).
# Usage: python3 tv22_build.py ops.json x22.json x22.txt sa.log out.json
import json, sys, re, itertools, random
from collections import deque
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
w = json.load(open(sys.argv[2])); A, E, CTL, data, hmr = w['A'], w['E'], w['CTL'], w['data'], w['hmr']; W = len(data)
L0 = open(sys.argv[3]).read().split('\n'); _, NCT, NC = map(int, L0[0].split())
cases = []
for l in L0[1:1 + NC]:
    a = list(map(int, l.split())); cases.append((a[0], a[1:1 + W], a[1 + W:1 + 2 * W]))
log = open(sys.argv[4]).read()
mm = re.search(r'^MU (\d+) 0x([0-9a-f]+)$', log, re.M); MU, SM = int(mm.group(1)), int(mm.group(2), 16)
gates = [(int(m.group(1), 16), int(m.group(2), 16), int(m.group(3))) for l in log.split('\n')
         for m in [re.match(r'tv \d+ 0x([0-9a-f]+) 0x([0-9a-f]+) (\d+)', l)] if m]
HB = ops[hmr][2]; Zi = data.index(22)
n = len(CTL); m = {c: 1 << i for i, c in enumerate(CTL)}
for i in range(A, E):
    o = ops[i]
    if K[o[0]] == 'CX' and o[1] in m: m[o[2]] ^= m[o[1]]
endst = tuple(m[c] for c in CTL); ident = tuple(1 << i for i in range(n))
par = lambda x: bin(x).count('1') & 1
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
    r = []
    for x in vs:
        for p in r: x = min(x, x ^ p)
        if x: r.append(x)
    return len(r)
def cx_synth(cols):
    rows = [sum(((cols[c] >> r) & 1) << c for c in range(W)) for r in range(W)]; seq = []
    for c in range(W):
        if not rows[c] >> c & 1:
            r = next(r for r in range(c + 1, W) if rows[r] >> c & 1); rows[c] ^= rows[r]; seq.append((r, c))
        for r in range(W):
            if r != c and rows[r] >> c & 1: rows[r] ^= rows[c]; seq.append((c, r))
    return seq
def tv_ops(L, v):
    a0 = bits(L)[0]; ker = [v]
    for j in range(W):
        e = 1 << j; e2 = e ^ (1 << a0) if (L >> j & 1) else e
        if e2 and rank(ker + [e2]) > len(ker): ker.append(e2)
    assert len(ker) == W - 1
    cols = [None] * W; cols[0] = 1 << a0; cols[1] = v; rest = iter(ker[1:])
    for j in range(W):
        if cols[j] is None: cols[j] = next(rest)
    return cx_synth(cols), 0, 1
def apply_cx(x, seq):
    for i, j in seq:
        if x >> i & 1: x ^= 1 << j
    return x
def ap(s, g, cs):
    Lm, v, f = g
    if not par(f & cs): return s
    a = 0
    for ww in range(W):
        if Lm >> ww & 1: a ^= s[ww]
    return [s[ww] ^ (a if v >> ww & 1 else 0) for ww in range(W)] if a else s
# --- exact fix-up solve ---
mono2 = [(0, 0)] + [(i, j) for i in range(1, NCT + 1) for j in range(i, NCT + 1)]
NV = (W - 1) * (NCT + 1) + len(mono2); eqs = []
for cs, st, en in cases:
    s = list(st)
    for t in range(len(gates) + 1):
        if t == MU:
            z = s[Zi]; s = [s[x] ^ (z if SM >> x & 1 else 0) for x in range(W)]; s[Zi] = 0; smu = list(s); zc = z
        if t < len(gates): s = ap(s, gates[t], cs)
    assert s == en, ('end mismatch', cs)
    mon = [1] + [cs >> i & 1 for i in range(NCT)]
    for t in range(W + 1):
        e = 0
        for x in range(W - 1):
            if smu[x] >> t & 1:
                for k in range(NCT + 1):
                    if mon[k]: e ^= 1 << (x * (NCT + 1) + k)
        if t == W:
            for q, (i, j) in enumerate(mono2):
                if mon[i] & mon[j]: e ^= 1 << ((W - 1) * (NCT + 1) + q)
        eqs.append((e, zc >> t & 1))
piv = {}
for e, r in eqs:
    for b in sorted(piv, reverse=True):
        if e >> b & 1: e ^= piv[b][0]; r ^= piv[b][1]
    if e: piv[e.bit_length() - 1] = (e, r)
    else: assert not r, 'z not fixable'
sol = 0
for b in sorted(piv):  # back-substitute (pivot = highest bit)
    e, r = piv[b]; rr = r ^ par((e & ~(1 << b)) & sol)
    if rr: sol |= 1 << b
for e, r in eqs: assert par(e & sol) == r
fix = []
for x in range(W - 1):
    for k in range(NCT + 1):
        if sol >> (x * (NCT + 1) + k) & 1:
            fix.append([KI['Z'], data[x], HB] if k == 0 else [KI['CZ'], CTL[k - 1], data[x], HB])
for q, (i, j) in enumerate(mono2):
    if sol >> ((W - 1) * (NCT + 1) + q) & 1:
        if i == 0: continue  # global phase
        fix.append([KI['Z'], CTL[i - 1], HB] if i == j else [KI['CZ'], CTL[i - 1], CTL[j - 1], HB])
# --- emit ---
st = ident; new = []; rnd = random.Random(1)
def emit(g):
    global st
    L, v, f = g; st, p = bfs(st, lambda s: f in s); new.extend(p); cw = CTL[st.index(f)]
    if L == v and bin(L).count('1') == 2:
        a, b = bits(L); new.append([KI['CSWAP'], cw, data[a], data[b], -1]); return
    S, a, b = tv_ops(L, v)
    for _ in range(200):
        x = rnd.getrandbits(W); y = apply_cx(x, S)
        if y >> a & 1: y ^= 1 << b
        y = apply_cx(y, S[::-1]); assert y == x ^ (v if par(L & x) else 0)
    new.extend([[KI['CX'], data[i], data[j], -1] for i, j in S]); new.append([KI['CCX'], cw, data[a], data[b], -1])
    new.extend([[KI['CX'], data[i], data[j], -1] for i, j in S[::-1]])
for g in gates[:MU]: emit(g)
st, p = bfs(st, lambda s: s == ident); new += p
new += [[KI['CX'], 22, data[x], -1] for x in range(W) if SM >> x & 1]
new.append([KI['HMR'], 22, HB, -1]); new += fix
for g in gates[MU:]: emit(g)
st, p = bfs(st, lambda s: s == endst); new += p
Zp = d['zpow_exact']; assert all(int(k) < A or int(k) >= E for k in Zp)
sh = len(new) - (E - A)
d['zpow_exact'] = {str(int(k) + (sh if int(k) >= E else 0)): v for k, v in Zp.items()}
d['ops'] = ops[:A] + new + ops[E:]; d['n_ops'] = len(d['ops']); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[5], 'w'))
print('gates', len(gates), 'MU', MU, 'S', hex(SM), 'fixups', len(fix), 'region ops', len(new), 'orig', E - A,
      'CSWAP', sum(K[o[0]] == 'CSWAP' for o in new), 'CCX', sum(K[o[0]] == 'CCX' for o in new))
