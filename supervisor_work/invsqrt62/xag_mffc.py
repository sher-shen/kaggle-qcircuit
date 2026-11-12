"""MFFC / leaf-dimension stats of the AND graph (xag_affine.py output) + output check by simulation.
For every AND node n: MFFC = ANDs whose every use lies inside the cone of n (n included).
Leaves = affine operand signals of MFFC ANDs with MFFC vars removed; dim = GF(2) rank of the
leaf masks (+const). A local re-synthesis can only win if |MFFC| > MCmax(dim)
(MCmax: dim<=2:1, 3:2, 4:3, 5:4, 6:6 [Calik/Turan/Peralta]).  Usage: xag_mffc.py xag.json"""
import json, sys
d = json.load(open(sys.argv[1]))
A = [(int(a, 16), ca, int(b, 16), cb) for a, ca, b, cb in d['ands']]
O = [(int(m, 16), c) for m, c in d['outs']]
N = len(A); NV = 8 + N
# simulate truth tables (256-bit ints)
FULL = (1 << 256) - 1
X = []
for i in range(8):
    t = 0
    for x in range(256):
        if (x >> i) & 1: t |= 1 << x
    X.append(t)
tt = list(X)
def ev(m, c):
    r = FULL if c else 0
    k = 0
    while m:
        if m & 1: r ^= tt[k]
        m >>= 1; k += 1
    return r
for a, ca, b, cb in A:
    tt.append(ev(a, ca) & ev(b, cb))
outs = [ev(m, c) for m, c in O]
# uses
uses = [[] for _ in range(N)]  # list of consumer AND idx or 'o'
for j, (a, ca, b, cb) in enumerate(A):
    for i in range(N):
        if ((a | b) >> (8 + i)) & 1: uses[i].append(j)
for m, c in O:
    for i in range(N):
        if (m >> (8 + i)) & 1: uses[i].append('o')
fan = [len(set(u)) for u in uses]
print('fanout hist', {k: fan.count(k) for k in sorted(set(fan))})
def rank(ms):
    basis = []
    for v in ms:
        for b in basis: v = min(v, v ^ b)
        if v: basis.append(v)
    return len(basis)
MC = {0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 6}
best = []
for n in range(N):
    m = {n}
    changed = True
    while changed:
        changed = False
        for i in range(n - 1, -1, -1):
            if i in m: continue
            if uses[i] and all(u != 'o' and u in m for u in uses[i]) and any(((A[j][0] | A[j][2]) >> (8 + i)) & 1 for j in m):
                m.add(i); changed = True
    mask_in = sum(1 << (8 + i) for i in m)
    leaves = []
    for j in m:
        a, ca, b, cb = A[j]
        leaves += [a & ~mask_in, b & ~mask_in]
    dim = rank([l for l in leaves if l])
    best.append((len(m) - MC.get(dim, 99), len(m), dim, n))
best.sort(reverse=True)
print('top (gain_bound, mffc, dim, node):', best[:15])
print('mffc size hist', {k: sum(1 for b in best if b[1] == k) for k in sorted(set(b[1] for b in best))})
json.dump({'tt': [hex(t) for t in tt], 'outs': [hex(o) for o in outs]}, open(sys.argv[1] + '.tt.json', 'w'))
