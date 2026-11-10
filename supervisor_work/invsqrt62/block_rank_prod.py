"""Sharper sound test for blocks left OPEN by block_rank.py with rank r == t-1 (a (t-1)-Toffoli rewrite would need K = r).
If P|D = (g_K..g_1 A)|D with K = r = dim R (R = span of output-bit residues mod V, V = affine functions on D), then
span{res f_1', ..., res f_K'} = R, and f_1 = a*b with a, b affine in x (A is affine) and res(a*b) != 0 (else rank < K).
So R must contain a nonzero residue of a product of two affine functions.  For fixed a, b -> a*b is GF(2)-linear in b, so
"(R+V) cap (Im_a+V) != V" is a rank test.  Same for the last gate: f_K is a product of two affine functions of the OUTPUT y
(a Toffoli's target is not among its controls, so f_K(y_{K-1}) = f_K(y_K)); test P^{-1} on P(D).
Verdict NONE(exact-necessary) if either side has no product; else PASS (not a proof that a rewrite exists).
Usage: block_rank_prod.py blocks.json idx1,idx2,... [reach.json ...] | --selftest n K seed"""
import sys, json, random
def pack(vals):  # list of 0/1 -> int
    v = 0
    for i, b in enumerate(vals):
        if b: v |= 1 << i
    return v
class Span:
    def __init__(self): self.rows = {}  # pivot bit -> row
    def add(self, r):
        while r:
            p = r.bit_length() - 1
            if p in self.rows: r ^= self.rows[p]
            else: self.rows[p] = r; return True
        return False
    def copy(self): s = Span(); s.rows = dict(self.rows); return s
    def dim(self): return len(self.rows)
def has_product(D, n, outs):
    """D: list of n-bit patterns, outs: list of output ints (pattern -> value) as packed bit-vectors over D"""
    N = len(D); ONE = (1 << N) - 1
    xs = [pack([(d >> j) & 1 for d in D]) for j in range(n)]
    aff_gen = [ONE] + xs
    V = Span(); [V.add(g) for g in aff_gen]; dV = V.dim()
    RV = V.copy(); [RV.add(o) for o in outs]; dRV = RV.dim()
    if dRV == dV: return None  # no residue at all
    # iterate all nonconstant linear parts of a (constant part: a and a+1 give products differing by b, affine -> same residue set
    # up to V; but a+1 = complement changes the product: (a+1)b = ab + b, b affine -> same residue. So constant bit irrelevant.)
    for m in range(1, 1 << n):
        a = 0
        for j in range(n):
            if (m >> j) & 1: a ^= xs[j]
        IV = V.copy(); [IV.add(a & g) for g in aff_gen]; dIV = IV.dim()
        if dIV == dV: continue
        S = RV.copy(); [S.add(r) for r in IV.rows.values()]
        if dRV + dIV - S.dim() > dV: return m
    return False
def test_block(perm, n, D):
    P = [perm[d] for d in D]
    outs = [pack([(p >> j) & 1 for p in P]) for j in range(n)]
    f = has_product(D, n, outs)
    # inverse on P(D): inputs are outputs
    Dinv = P; outs_inv = [pack([(d >> j) & 1 for d in D]) for j in range(n)]
    b = has_product(Dinv, n, outs_inv)
    return f, b
def rand_circ(n, K, rng):
    # random affine A (as sequence of CX/X) then K random CCX; returns perm list
    gates = []
    for _ in range(4 * n):
        i, j = rng.sample(range(n), 2); gates.append(('CX', i, j))
    for j in range(n):
        if rng.random() < .5: gates.append(('X', j))
    for _ in range(K):
        a, b, c = rng.sample(range(n), 3); gates.append(('CCX', a, b, c))
        for _ in range(n):
            i, j = rng.sample(range(n), 2); gates.append(('CX', i, j))
    T = []
    for x in range(1 << n):
        y = x
        for g in gates:
            if g[0] == 'X': y ^= 1 << g[1]
            elif g[0] == 'CX': y ^= ((y >> g[1]) & 1) << g[2]
            else: y ^= (((y >> g[1]) & (y >> g[2])) & 1) << g[3]
        T.append(y)
    return T
if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        n, K, seed = map(int, sys.argv[2:5]); rng = random.Random(seed)
        for t in range(int(sys.argv[5]) if len(sys.argv) > 5 else 4):
            T = rand_circ(n, K, rng); D = list(range(1 << n))
            if t >= 2: D = sorted(rng.sample(D, len(D) // 2))
            P = [T[d] for d in D]; RV = Span(); ONE = (1 << len(D)) - 1
            [RV.add(g) for g in [ONE] + [pack([(d >> j) & 1 for d in D]) for j in range(n)]]; dV = RV.dim()
            [RV.add(pack([(p >> j) & 1 for p in P])) for j in range(n)]; r = RV.dim() - dV
            f, bk = test_block(T, n, D)
            print('planted n', n, 'K', K, '|D|', len(D), 'rank', r, 'fwd', f is not False, 'bwd', bk is not False,
                  '' if r < K else ('OK' if (f is not False and bk is not False) else 'SOUNDNESS-FAIL'))
        for t in range(3):
            T = list(range(1 << n)); rng.shuffle(T); D = list(range(1 << n))
            print('random perm n', n, 'fwd/bwd', test_block(T, n, D))
        sys.exit()
    blocks = json.load(open(sys.argv[1])); idx = [int(i) for i in sys.argv[2].split(',')]
    reach = [json.load(open(f)) for f in sys.argv[3:]]
    for bi in idx:
        b = blocks[bi]; n = len(b['W'])
        D = sorted(set().union(*[set(rr[bi]['reach']) for rr in reach])) if reach else list(range(1 << n))
        f, bk = test_block(b['perm'], n, D)
        v = 'NONE(exact-necessary)' if (f is False or bk is False) else 'PASS'
        print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b['tof'], '|D|', len(D), 'fwd', f, 'bwd', bk, v, flush=True)
