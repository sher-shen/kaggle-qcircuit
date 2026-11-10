"""Exact enumeration: is the dirty-CCCX block map P (wires a=q28,b=q17,s=q19,t=q25,d=q0 dirty; P: s^=ab, t^=abs)
equal to g1 g2 g3 A with A affine (any CNOT/X circuit) and g_i Toffoli-conjugates?  Every Toffoli conjugated by an affine
map is x -> x + v [x in F], F a codim-2 flat, v a nonzero vector in F's direction space: 620 flats x 7 = 4340 gates on 5 wires.
P = g1 g2 g3 A  <=>  h = g2 g1 P = g3 A  <=>  g3 h is affine.  Usage: cccx_enum.py [selftest]"""
import sys, itertools, numpy as np
n = 5; N = 1 << n
X = np.arange(N)
def bit(x, j): return (x >> j) & 1
def P_tab():
    out = []
    for x in range(N):
        a, b, s, t, d = (bit(x, j) for j in range(5))
        s2 = s ^ (a & b); t2 = t ^ (a & b & s)
        out.append(a | b << 1 | s2 << 2 | t2 << 3 | d << 4)
    return np.array(out)
pc = np.array([bin(i).count('1') for i in range(N)])
# linear forms u (as masks); flat F = {x: u1.x = c1, u2.x = c2}
dot = lambda u: pc[X & u] & 1
gates = []
seen = set()
for u1, u2 in itertools.combinations(range(1, N), 2):
    U = frozenset([u1, u2, u1 ^ u2])
    for c1 in (0, 1):
        for c2 in (0, 1):
            ind = (dot(u1) == c1) & (dot(u2) == c2)
            key = ind.tobytes()
            for vv in range(1, N):
                if pc[vv & u1] & 1 or pc[vv & u2] & 1: continue
                k2 = (key, vv)
                if k2 in seen: continue
                seen.add(k2); gates.append(np.where(ind, X ^ vv, X))
G = np.array(gates); print('gates', len(G), flush=True)
# affine test for a batch of tables (rows): f affine iff f(x)^f(0) is linear: f(x)^f(0) == xor of f(e_j)^f(0) over set bits
def is_affine(T):
    f0 = T[:, :1]; lin = np.zeros_like(T)
    for j in range(n):
        col = (T[:, [1 << j]] ^ f0)
        lin ^= np.where(bit(X, j)[None, :] == 1, col, 0)
    return np.all((T ^ f0) == lin, axis=1)
def search(P):
    hits = []
    for i1 in range(len(G)):
        g1P = G[i1][P]                 # g1(P(x))
        H = G[:, g1P]                  # g2(g1(P(x))) for all g2
        # cheap filter: degree <= 2 of every output bit (g3 A has degree <= 2)
        ok = np.ones(len(G), bool)
        for j in range(n):
            a = bit(H, j).astype(np.uint8)
            for k in range(n):        # Moebius transform
                m = bit(X, k) == 1
                a[:, m] ^= a[:, X[m] ^ (1 << k)]
            ok &= ~np.any(a[:, pc >= 3], axis=1)
        for i2 in np.nonzero(ok)[0]:
            h = H[i2]
            aff = is_affine(G[:, h])
            if aff.any():
                hits.append((i1, int(i2), int(np.nonzero(aff)[0][0]))); return hits
    return hits
if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
    rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    while True:
        cols = [int(c) for c in rng.integers(0, N, n)]
        A = np.array([int(np.bitwise_xor.reduce([cols[c] for c in range(n) if (x >> c) & 1] + [0])) ^ 5 for x in range(N)])
        if len(set(A.tolist())) == N: break
    i, j, k = rng.integers(0, len(G), 3)
    Pp = G[i][G[j][G[k][A]]]
    print('selftest planted', i, j, k, '->', search(Pp))
else:
    print('P hits (3 Toffolis):', search(P_tab()))
