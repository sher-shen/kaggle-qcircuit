"""Exact recursive search "P|D = g_K .. g_1 A" for blocks where the residue rank stays == K (see block_rank_prod.py).
WLOG P = Q o T with T(x) = x + w a(x) b(x) (T = A^-1 g_1 A), a, b linear functionals (constants and the basis of U = span{a,b}
only change T by an invertible affine map, which Q absorbs), w != 0 with a(w) = b(w) = 0 (target not a control).
Then Q|T(D) = P o T|T(D) has K-1 gates.  At each level: rank r of the residues; r == 0 -> affine (HIT); r > K -> dead;
r == K -> res(ab) must lie in R (exact pruning); r < K -> SLACK (reported, not searched: the pruning is not valid there).
CSWAP-type gates (x + w c (a)), w = e_i + e_j) are the same form with U = span{c, x_i + x_j}... they are included since
any (U, w) with w in ker U is enumerated.
Usage: block_peel.py blocks.json idx K [reach.json ...] | --selftest n K seed trials"""
import sys, json, random
import numpy as np
def par(x, m):
    v = x & m; c = np.zeros(len(x), np.uint8)
    while True:
        nz = v != 0
        if not nz.any(): return c
        c[nz] ^= 1; v = v & (v - 1)
def packbits(arr):
    return int.from_bytes(np.packbits(arr.astype(np.uint8), bitorder='little').tobytes(), 'little')
class Span:
    def __init__(self, rows=None): self.rows = dict(rows) if rows else {}
    def add(self, r):
        while r:
            p = r.bit_length() - 1
            if p in self.rows: r ^= self.rows[p]
            else: self.rows[p] = r; return True
        return False
    def dim(self): return len(self.rows)
stats = {'nodes': 0, 'slack': 0}
def level(D, P, n, K, path, out, limit):
    stats['nodes'] += 1
    N = len(D); ONE = (1 << N) - 1
    lin = {}
    def L(m):
        if m not in lin: lin[m] = packbits(par(D, m))
        return lin[m]
    xs = [L(1 << j) for j in range(n)]
    V = Span(); V.add(ONE); [V.add(x) for x in xs]; dV = V.dim()
    RV = Span(V.rows); [RV.add(packbits((P >> j) & 1)) for j in range(n)]; r = RV.dim() - dV
    if r == 0: out.append(list(path)); return True
    if r > K: return False
    if r < K: stats['slack'] += 1; out.append(['SLACK', K, r] + list(path)); return False
    full = (1 << n) - 1
    for m1 in range(1, full + 1):
        a = L(m1)
        for m2 in range(m1 + 1, full + 1):
            m3 = m1 ^ m2
            if m3 < m2: continue  # canonical subspace: m1 < m2 < m1^m2
            if m1 > m3: continue
            ab = a & L(m2)
            S = Span(RV.rows)
            if S.add(ab):  # ab not in R+V
                continue
            if Span(V.rows).add(ab) is False:  # ab affine -> no-op gate
                continue
            # targets w with parity(w&m1)=parity(w&m2)=0
            f = (par(D, m1) & par(D, m2)).astype(np.int64)
            for w in range(1, full + 1):
                if bin(w & m1).count('1') & 1 or bin(w & m2).count('1') & 1: continue
                TD = D ^ (f * w)
                # Q on T(D) = P o T: at point T(x), Q = P(x)  (T involution)
                path.append((m1, m2, w))
                if level(TD, P, n, K - 1, path, out, limit) and len([o for o in out if o[0] != 'SLACK']) >= limit:
                    path.pop(); return True
                path.pop()
    return any(o[0] != 'SLACK' for o in out)
def run(perm, n, D, K, limit=1):
    D = np.asarray(D, np.int64); P = np.asarray(perm, np.int64)[D]; out = []
    stats['nodes'] = 0; stats['slack'] = 0
    level(D, P, n, K, [], out, limit)
    hits = [o for o in out if o[0] != 'SLACK']; sl = [o for o in out if o[0] == 'SLACK']
    return hits, sl
def rand_circ(n, K, rng):
    gates = []
    for _ in range(4 * n):
        i, j = rng.sample(range(n), 2); gates.append(('CX', i, j))
    for _ in range(K):
        a, b, c = rng.sample(range(n), 3); gates.append(('CCX', a, b, c))
        for _ in range(n):
            i, j = rng.sample(range(n), 2); gates.append(('CX', i, j))
    T = []
    for x in range(1 << n):
        y = x
        for g in gates:
            if g[0] == 'CX': y ^= ((y >> g[1]) & 1) << g[2]
            else: y ^= (((y >> g[1]) & (y >> g[2])) & 1) << g[3]
        T.append(y)
    return T
if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        n, K, seed, tr = map(int, sys.argv[2:6]); rng = random.Random(seed)
        for t in range(tr):
            T = rand_circ(n, K, rng)
            h, sl = run(T, n, range(1 << n), K)
            h2, _ = run(T, n, range(1 << n), K - 1)
            print('planted n', n, 'K', K, 'HIT' if h else ('SLACK' if sl else 'MISS'), 'nodes', stats['nodes'],
                  '| K-1:', 'HIT' if h2 else ('SLACK' if _ else 'NONE'), flush=True)
        sys.exit()
    blocks = json.load(open(sys.argv[1])); bi = int(sys.argv[2]); K = int(sys.argv[3])
    reach = [json.load(open(f)) for f in sys.argv[4:]]
    b = blocks[bi]; n = len(b['W'])
    D = sorted(set().union(*[set(rr[bi]['reach']) for rr in reach])) if reach else list(range(1 << n))
    h, sl = run(b['perm'], n, D, K)
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b['tof'], 'K', K, '|D|', len(D), 'nodes', stats['nodes'],
          'HIT ' + str(h[0]) if h else ('NONE(exact)' if not sl else 'SLACK-ONLY %d' % len(sl)), flush=True)
