"""cccx_enum.py generalised to n wires (wires 5.. are extra dirty wires that must be restored) + quadratic-structure filter:
g3 A = affine + v*(l*m), so every output bit of h = g2 g1 P has degree <= 2 and all nonzero quadratic parts equal one form of rank 2.
Survivors get the full test (g3 h affine for some g3). Usage: cccx_enum_n.py n nproc [selftest seed]"""
import sys, itertools, numpy as np
from multiprocessing import Pool
n = int(sys.argv[1]); NP = int(sys.argv[2]); N = 1 << n; X = np.arange(N)
bit = lambda x, j: (x >> j) & 1
pc = np.array([bin(i).count('1') for i in range(N)])
Q2 = np.nonzero(pc == 2)[0]
def P_tab():
    out = X.copy()
    a, b, s = bit(X, 0), bit(X, 1), bit(X, 2)
    out = out ^ ((a & b) << 2) ^ ((a & b & s) << 3); return out
dot = lambda u: pc[X & u] & 1
def build():
    gates, seen = [], set()
    for u1, u2 in itertools.combinations(range(1, N), 2):
        for c1 in (0, 1):
            for c2 in (0, 1):
                ind = (dot(u1) == c1) & (dot(u2) == c2)
                for vv in range(1, N):
                    if pc[vv & u1] & 1 or pc[vv & u2] & 1: continue
                    k = (ind.tobytes(), vv)
                    if k in seen: continue
                    seen.add(k); gates.append(np.where(ind, X ^ vv, X).astype(np.int16))
    return np.array(gates)
G = build()
def is_affine(T):
    f0 = T[:, :1]; lin = np.zeros_like(T)
    for j in range(n): lin ^= np.where(bit(X, j)[None, :] == 1, T[:, [1 << j]] ^ f0, 0)
    return np.all((T ^ f0) == lin, axis=1)
def rank2(qv):  # quadratic ANF coeffs (monomials Q2) -> rank of alternating matrix == 2
    M = np.zeros((n, n), np.uint8)
    for c, m in zip(qv, Q2):
        if c: i, j = [k for k in range(n) if m >> k & 1]; M[i, j] = M[j, i] = 1
    r = 0; M = M.copy()
    for col in range(n):
        piv = [i for i in range(r, n) if M[i, col]]
        if not piv: continue
        M[[r, piv[0]]] = M[[piv[0], r]]
        for i in range(n):
            if i != r and M[i, col]: M[i] ^= M[r]
        r += 1
    return r == 2
P = None
def work(i1):
    g1P = G[i1][P]; H = G[:, g1P]; ok = np.ones(len(G), bool); quad = None
    qs = []
    for j in range(n):
        a = bit(H, j).astype(np.uint8)
        for k in range(n):
            m = bit(X, k) == 1; a[:, m] ^= a[:, X[m] ^ (1 << k)]
        ok &= ~np.any(a[:, pc >= 3], axis=1); qs.append(a[:, Q2])
    qs = np.stack(qs, 1)  # (G, n, |Q2|)
    nz = qs.any(2)
    ref = qs[np.arange(len(G)), nz.argmax(1)]
    ok &= np.all(~nz[:, :, None] | (qs == ref[:, None, :]), axis=(1, 2)) & nz.any(1)
    for i2 in np.nonzero(ok)[0]:
        if not rank2(ref[i2]): continue
        aff = is_affine(G[:, H[i2]])
        if aff.any(): return (i1, int(i2), int(np.nonzero(aff)[0][0]))
    return None
def init(p):
    global P; P = p
if __name__ == '__main__':
    print('n', n, 'gates', len(G), flush=True)
    if len(sys.argv) > 3:
        rng = np.random.default_rng(int(sys.argv[4]))
        while True:
            cols = [int(c) for c in rng.integers(0, N, n)]
            A = np.array([int(np.bitwise_xor.reduce([cols[c] for c in range(n) if (x >> c) & 1] + [0])) ^ 5 for x in range(N)])
            if len(set(A.tolist())) == N: break
        i, j, k = rng.integers(0, len(G), 3); Pt = G[i][G[j][G[k][A]]]; print('planted', i, j, k)
    else: Pt = P_tab()
    with Pool(NP, init, (Pt,)) as pool:
        for r in pool.imap_unordered(work, range(len(G)), chunksize=16):
            if r: print('HIT', r, flush=True); pool.terminate(); break
        else: print('NONE (exact): no 3-Toffoli circuit on', n, 'wires', flush=True)
