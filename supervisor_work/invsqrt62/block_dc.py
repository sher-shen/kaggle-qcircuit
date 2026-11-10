"""block_enum.py with don't-cares: test whether a block permutation P, restricted to its reachable entry set D
(block_reach.py), equals (g_K ... g_1 A)|D with K = tof-1 (also K = tof-2), A affine on the full 2^n space.
Brute force (no quadratic filter, it is not valid on a subset): K=0 affine-on-D, K=1 all g, K=2 all g1 x vectorised g2.
Usage: block_dc.py reach.json [reach2.json ...] -- n nproc maxK   (D = union of the reach sets)"""
import sys, json, numpy as np
from multiprocessing import Pool
sep = sys.argv.index('--'); files = sys.argv[1:sep]; n, NP, MAXK = map(int, sys.argv[sep + 1:sep + 4])
sys.argv = ['x', 'none', str(n), '1']
exec(open(__file__.replace('block_dc.py', 'block_enum.py')).read().split("if __name__")[0])
def affine_checker(D):
    d0 = D[0]; basis = {}; rows = []  # basis: pivot -> (vec, combo mask over basis points)
    pts = []
    for x in D:
        v = x ^ d0; c = 0
        while v:
            h = v.bit_length() - 1
            if h in basis: bv, bc = basis[h]; v ^= bv; c ^= bc
            else: basis[h] = (v, c ^ (1 << len(pts))); pts.append(x); v = 0; c = None
        rows.append(c)  # None -> x is a new basis point
    idx = {x: i for i, x in enumerate(D)}; P_idx = [idx[p] for p in pts]
    combos = []
    for i, c in enumerate(rows):
        if c is None: continue
        combos.append((i, [P_idx[j] for j in range(len(pts)) if c >> j & 1]))
    def check(T):  # T (m, |D|) -> bool mask
        T = np.atleast_2d(T); ok = np.ones(len(T), bool); f0 = T[:, 0]
        for i, sel in combos:
            pred = f0.copy() if len(sel) % 2 == 0 else np.zeros_like(f0)
            for j in sel: pred ^= T[:, j]
            ok &= (pred == T[:, i])
        return ok
    return check
CHK = None; PD = None
def init(c, p):
    global CHK, PD; CHK, PD = c, p
def w2(i1):
    H = G[i1][PD]; a = CHK(G[:, H])
    return (i1, int(np.nonzero(a)[0][0])) if a.any() else None
if __name__ == '__main__':
    B = [json.load(open(f)) for f in files]
    for bi, b in enumerate(B[0]):
        if len(b['W']) != n: continue
        D = sorted(set().union(*[set(bb[bi]['reach']) for bb in B]))
        if not D: print(bi, 'never executed'); continue
        P = np.array(b['perm'], np.int16); PDl = P[np.array(D)]; chk = affine_checker(D); t = b['tof']; res = []
        for K in range(max(0, t - 2), t):
            if K > MAXK: continue
            if K == 0: r = True if chk(PDl[None, :])[0] else None
            elif K == 1:
                a = chk(G[:, PDl]); r = int(np.nonzero(a)[0][0]) if a.any() else None
            else:
                with Pool(NP, init, (chk, PDl)) as pool:
                    r = next((x for x in pool.imap_unordered(w2, range(len(G)), chunksize=64) if x), None)
            res.append(f'K{K}:' + ('HIT ' + str(r) if r is not None else 'NONE'))
        print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'W', b['W'], 'tof', t, '|D|', len(D), ' '.join(res), flush=True)
