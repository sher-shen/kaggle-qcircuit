"""Large-window K=1 test (2->1, 3->1 Toffoli rewrites) with entry don't-cares, no gate table needed.
Necessary condition for P|D = (g A)|D (g = x -> x + v[x in F]): modulo V = affine functions restricted to D, every output
bit's residue is 0 or one common r (r = residue of q(x) = [A(x) in F], a product of two affine functions).  Blocks passing
this weak test are then checked for r in {residues of a*b} and, if n <= 7, exactly with block_dc's checker.
Usage: block_k1_big.py reach1.json [reach2.json ...] -- minn maxn"""
import sys, json, numpy as np
sep = sys.argv.index('--'); files = sys.argv[1:sep]; MINN, MAXN = map(int, sys.argv[sep + 1:sep + 3])
pcnt = np.array([bin(i).count('1') & 1 for i in range(1 << 12)], np.uint8)
def basis(D, n):
    Dn = np.array(D); rows = [np.ones(len(D), np.uint8)] + [((Dn >> j) & 1).astype(np.uint8) for j in range(n)]
    B, piv = [], []
    for r in rows:
        r = r.copy()
        for b, p in zip(B, piv):
            if r[p]: r ^= b
        nz = np.nonzero(r)[0]
        if not len(nz): continue
        p = nz[0]
        for i in range(len(B)):
            if B[i][p]: B[i] ^= r
        B.append(r); piv.append(p)
    return np.array(B, np.int32), piv
def red(F, B, piv):
    F = F.astype(np.uint8); return F ^ ((F[:, piv].astype(np.int32) @ B) & 1).astype(np.uint8)
def in_products(r, D, n, B, piv):
    Dn = np.array(D); aff = np.array([(pcnt[Dn & (m >> 1)] ^ (m & 1)) for m in range(1 << (n + 1))], np.uint8)
    for i in range(len(aff)):
        R = red(aff[i][None, :] & aff[i:], B, piv)
        if np.any(np.all(R == r[None, :], 1)): return True
    return False
if __name__ == '__main__':
    Bs = [json.load(open(f)) for f in files]; stats = {}
    for bi, b in enumerate(Bs[0]):
        n = len(b['W'])
        if not (MINN <= n <= MAXN): continue
        D = sorted(set().union(*[set(bb[bi]['reach']) for bb in Bs]))
        if not D: continue
        P = np.array(b['perm'], np.int64)[np.array(D)]; B, piv = basis(D, n)
        R = red(np.array([(P >> j) & 1 for j in range(n)]), B, piv)
        nzr = [r for r in R if r.any()]
        if not nzr: verdict = 'K0-affine-on-D(HIT)'
        elif any(np.any(r != nzr[0]) for r in nzr): verdict = 'NONE'
        elif in_products(nzr[0], D, n, B, piv): verdict = 'CANDIDATE'
        else: verdict = 'NONE(not-product)'
        stats[(n, b['tof'], verdict)] = stats.get((n, b['tof'], verdict), 0) + 1
        if verdict != 'NONE':
            print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'W', b['W'], 'tof', b['tof'], '|D|', len(D), 'dimV', len(piv), verdict, flush=True)
    for k in sorted(stats): print('n %d tof %d %s: %d' % (k + (stats[k],)))
