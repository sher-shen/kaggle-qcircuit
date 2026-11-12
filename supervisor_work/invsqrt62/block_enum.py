"""Exact test: can a block permutation P on n wires (from block_extract.py) be built with K = tof-1 Toffolis + any
affine (CX/X/SWAP) layers?  Any such circuit is P = g_K ... g_1 A with g_i affine-conjugated Toffolis
(x -> x + v [x in F], F a codim-2 flat, v in F's direction) -- same gate set as cccx_enum_n.py.
K=0: P affine. K=1: exists g with g P affine. K=2: loop g, test K=1 on gP (quadratic filter first). K=3: cccx_enum_n.
Usage: block_enum.py blocks.json n nproc [selftest seed [Ks e.g. 12]]"""
import sys, json, itertools, numpy as np
from multiprocessing import Pool
n = int(sys.argv[2]); NP = int(sys.argv[3]); N = 1 << n; X = np.arange(N)
bit = lambda x, j: (x >> j) & 1
pc = np.array([bin(i).count('1') for i in range(N)]); Q2 = np.nonzero(pc == 2)[0]
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
    T = np.atleast_2d(T); f0 = T[:, :1]; lin = np.zeros_like(T)
    for j in range(n): lin ^= np.where(bit(X, j)[None, :] == 1, T[:, [1 << j]] ^ f0, 0)
    return np.all((T ^ f0) == lin, axis=1)
def anf_q(H):  # H (m,N) -> ok mask (deg<=2) and quad coeffs (m,n,|Q2|)
    ok = np.ones(len(H), bool); qs = []
    for j in range(n):
        a = bit(H, j).astype(np.uint8)
        for k in range(n):
            m = bit(X, k) == 1; a[:, m] ^= a[:, X[m] ^ (1 << k)]
        ok &= ~np.any(a[:, pc >= 3], axis=1); qs.append(a[:, Q2])
    return ok, np.stack(qs, 1)
def rank2(qv):
    M = np.zeros((n, n), np.uint8)
    for c, m in zip(qv, Q2):
        if c: i, j = [k for k in range(n) if m >> k & 1]; M[i, j] = M[j, i] = 1
    r = 0
    for col in range(n):
        piv = [i for i in range(r, n) if M[i, col]]
        if not piv: continue
        M[[r, piv[0]]] = M[[piv[0], r]]
        for i in range(n):
            if i != r and M[i, col]: M[i] ^= M[r]
        r += 1
    return r == 2
def one_tof_ok(H):  # rows of H that pass the 1-Toffoli necessary filter
    ok, qs = anf_q(H); nz = qs.any(2); ref = qs[np.arange(len(H)), nz.argmax(1)]
    ok &= np.all(~nz[:, :, None] | (qs == ref[:, None, :]), axis=(1, 2)) & nz.any(1)
    return [i for i in np.nonzero(ok)[0] if rank2(ref[i])]
def k1(P):
    if not one_tof_ok(P[None, :]): return None
    a = is_affine(G[:, P]); return int(np.nonzero(a)[0][0]) if a.any() else None
def work(args):
    P, K, i1 = args
    if K == 2:
        h = G[i1][P]; r = k1(h); return (i1, r) if r is not None else None
    g1P = G[i1][P]; H = G[:, g1P]
    for i2 in one_tof_ok(H):
        aff = is_affine(G[:, H[i2]])
        if aff.any(): return (i1, int(i2), int(np.nonzero(aff)[0][0]))
    return None
def test(P, K, pool):
    P = np.asarray(P, np.int16)
    if K == 0: return True if is_affine(P)[0] else None
    if K == 1: return k1(P)
    for r in pool.imap_unordered(work, ((P, K, i) for i in range(len(G))), chunksize=32):
        if r: return r
    return None
def rand_affine(rng):
    while True:
        cols = [int(c) for c in rng.integers(0, N, n)]; c0 = int(rng.integers(N))
        A = np.array([int(np.bitwise_xor.reduce([cols[c] for c in range(n) if (x >> c) & 1] + [0])) ^ c0 for x in range(N)])
        if len(set(A.tolist())) == N: return A.astype(np.int16)
if __name__ == '__main__':
    blocks = [b for b in json.load(open(sys.argv[1])) if len(b['W']) == n]
    print('n', n, 'gates', len(G), 'blocks', len(blocks), flush=True)
    with Pool(NP) as pool:
        if len(sys.argv) > 4:
            rng = np.random.default_rng(int(sys.argv[4]))
            for K in [int(k) for k in (sys.argv[5] if len(sys.argv) > 5 else "123")]:
                A = rand_affine(rng); P = A
                for i in rng.integers(0, len(G), K): P = G[i][P]
                print('selftest K', K, 'HIT' if test(P, K, pool) is not None else 'MISS', flush=True)
            sys.exit()
        for bi, b in enumerate(blocks):
            K = b['tof'] - 1
            if K > 3: print(bi, 'skip K', K); continue
            r = test(b['perm'], K, pool)
            print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'W', b['W'], 'tof', b['tof'], '->', 'HIT ' + str(r) if r not in (None, False) else 'NONE(exact)', flush=True)
