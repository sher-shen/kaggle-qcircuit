"""Fast sound K=1 / K=2 test for block permutations with entry don't-cares (directive 2 of SUPERVISOR 11-10 07:50).
K=1 relaxation: if P|D = (g A)|D with g a Toffoli-class gate x -> x + v[x in F] (F codim-2 flat, v in F's direction),
then on D: P_j(x) = A_j(x) + v_j q(x) with q(x) = [A(x) in F] a product of two affine functions of x.  So, modulo the
space V of affine functions restricted to D, every output bit's residue is 0 or one common r, and r lies in the set S of
residues of products of two affine functions.  Failing this test => no K=1 form (exact NONE).  Passing => candidate, which
is then checked exactly with block_dc's full affine_checker over all gates.
K=2: P = g2 g1 A  <=>  g2 P = g1 A (g2 involution): loop g2 over all gates G, apply the K=1 relaxation to g2 P (vectorised).
Usage: block_dc_res.py blocks_with_reach.json [more reach files ...] -- n maxK [selftest]"""
import sys, json, itertools, numpy as np
sep = sys.argv.index('--'); files = sys.argv[1:sep]; n = int(sys.argv[sep + 1]); MAXK = int(sys.argv[sep + 2])
SELF = len(sys.argv) > sep + 3
sys.argv = ['x', 'none', str(n), '1']
exec(open(__file__.replace('block_dc_res.py', 'block_enum.py')).read().split("if __name__")[0])  # G, N, X, n
_src = open(__file__.replace('block_dc_res.py', 'block_dc.py')).read()
exec('def affine_checker' + _src.split('def affine_checker')[1].split('CHK = None')[0])  # exact checker from block_dc.py

def gf2_basis(D):
    """Rows = affine functions on D (const + n bits), reduced echelon with pivots. Returns (B (k,|D|) uint8, piv list)."""
    Dn = np.array(D); rows = [np.ones(len(D), np.uint8)] + [((Dn >> j) & 1).astype(np.uint8) for j in range(n)]
    B = []; piv = []
    for r in rows:
        r = r.copy()
        for b, p in zip(B, piv):
            if r[p]: r ^= b
        nz = np.nonzero(r)[0]
        if len(nz) == 0: continue
        p = nz[0]
        for i in range(len(B)):
            if B[i][p]: B[i] ^= r
        B.append(r); piv.append(p)
    return np.array(B), piv

class Res:
    def __init__(self, D):
        self.B, self.piv = gf2_basis(D); self.D = np.array(D)
        Dn = self.D; aff = []
        for m in range(1 << (n + 1)):  # affine fn c + u.x
            u = m >> 1; aff.append(((pc[Dn & u] & 1) ^ (m & 1)).astype(np.uint8))
        aff = np.array(aff); S = set()
        for i in range(len(aff)):
            pr = aff[i][None, :] & aff[i:]; R = self.red(pr)
            for r in R:
                if r.any(): S.add(r.tobytes())
        self.S = S
    def red(self, F):  # F (m,|D|) uint8 -> residues
        F = F.astype(np.uint8)
        return F ^ ((F[:, self.piv].astype(np.int32) @ self.B.astype(np.int32)) & 1).astype(np.uint8)
    def k1_relax(self, H):
        """H (m,|D|) int values -> bool mask: passes the K=1 (or K=0) necessary condition."""
        m = len(H); ok = np.ones(m, bool); common = np.zeros((m, len(self.D)), np.uint8); have = np.zeros(m, bool)
        Rs = [self.red(((H >> j) & 1)) for j in range(n)]
        for R in Rs:
            nz = R.any(1)
            first = nz & ~have; common[first] = R[first]; have |= nz
            ok &= ~(nz & have & ~first & np.any(R != common, 1))
        # residue r must be in S (or zero -> affine, K=0)
        for i in np.nonzero(ok & have)[0]:
            if common[i].tobytes() not in self.S: ok[i] = False
        return ok

def run_block(P, D, t, CH=20000):
    D = sorted(D); PD = P[np.array(D)]; rs = Res(D); out = []
    chk = affine_checker(D)
    for K in range(max(0, t - 2), t):
        if K > MAXK or K == 0: continue
        if K == 1:
            cand = rs.k1_relax(PD[None, :])[0]
            if not cand: out.append('K1:NONE'); continue
            a = chk(G[:, PD]); out.append('K1:' + ('HIT %d' % int(np.nonzero(a)[0][0]) if a.any() else 'NONE(relaxpass)')); continue
        # K == 2
        hits = []; npass = 0
        for s in range(0, len(G), CH):
            H = G[s:s + CH][:, PD]  # g2 P on D
            m = rs.k1_relax(H); idx = np.nonzero(m)[0]; npass += len(idx)
            for i in idx:
                a = chk(G[:, H[i]])
                if a.any(): hits.append((s + i, int(np.nonzero(a)[0][0]))); break
            if hits: break
        out.append('K2:' + ('HIT %s' % (hits[0],) if hits else 'NONE(relaxpass %d)' % npass))
    return out

if __name__ == '__main__':
    print('n', n, '|G|', len(G), flush=True)
    if SELF:  # plant P = g2 g1 A on a random D, expect K1 HIT for t=2 / K2 HIT for t=3
        rng = np.random.default_rng(int(sys.argv[-1]) if sys.argv[-1].isdigit() else 1)
        for trial in range(3):
            while True:
                M = rng.integers(0, 2, (n, n))
                if round(abs(np.linalg.det(M))) % 2 == 1: break
            c = int(rng.integers(0, N))
            A = np.array([int(np.bitwise_xor.reduce([((x >> j) & 1) * int(sum(M[i, j] << i for i in range(n))) for j in range(n)] + [c])) for x in range(N)])
            g1 = G[rng.integers(len(G))]; g2 = G[rng.integers(len(G))]
            D = sorted(rng.choice(N, size=min(N, 40 + 20 * trial), replace=False).tolist())
            print('plant K1', run_block(g1[A], D, 2), 'plant K2', run_block(g2[g1[A]], D, 3), flush=True)
        sys.exit()
    B = [json.load(open(f)) for f in files]
    import os; SH = os.environ.get('SHARD')  # "i/k": only blocks with bi % k == i
    for bi, b in enumerate(B[0]):
        if len(b['W']) != n: continue
        if SH and bi % int(SH.split('/')[1]) != int(SH.split('/')[0]): continue
        D = sorted(set().union(*[set(bb[bi]['reach']) for bb in B]))
        if not D: print(bi, 'never executed'); continue
        P = np.array(b['perm'], np.int64)
        res = run_block(P, D, b['tof'])
        print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'W', b['W'], 'tof', b['tof'], '|D|', len(D), ' '.join(res), flush=True)
