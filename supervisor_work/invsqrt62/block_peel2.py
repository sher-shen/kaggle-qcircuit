"""Exact peel search "P|D = g_K .. g_1 A" (same question as block_peel.py), fast enough for n = 20.
Work in the affine-hull coordinates y of D (dim m).  One level, with W = span{1, Y_j, P_j} on D, r = dim W - (m+1):
 r == 0 -> HIT, r > K -> dead.  First gate T(y) = y + w a(y) b(y) (a, b affine: all 4 constant choices are tried, w in the linear hull, a(w) = b(w) = 0).
 (1) Q|T(D) has rank r-1 only if ab in W  <=>  the alternating form c = a ^ b lies in Z = {c : sum c_ij red_W(y_i y_j) = 0}
     (linear in b for fixed a; all a enumerated in C, ab_enum.c).
 (2) Pull back to D: affine functions on T(D) become span{1, Y_j + w_j ab}; the rank drops by one iff ab is not in that
     span + P.  Case A (w in the linear hull of D): iff w . C0 = 0 and w . c0 = 1 where C0 = {c : sum c_j Y_j in span(1,P)}, c0 any c with ab + sum c_j Y_j in
     span(1,P).  So the targets w form an affine space (plus a(w) = b(w) = 0), no 2^n loop.  Rank can drop by at most one,
     so there is no SLACK below the root.  Case B (w outside the hull, e.g. a target wire that is constant on D): the rank
     always drops; all such w are equivalent, so D gets one fresh coordinate holding ab (hull dim m+1 <= n).  Recurse on T(D) with the same P values.
Usage: block_peel2.py ab_enum_bin blocks.json idx K reach.json [reach2.json ...] | --selftest ab_enum_bin n K seed trials"""
import sys, json, random, subprocess, itertools
import numpy as np
def rref_add(piv, v):
    for p, r in piv.items():
        if (v >> p) & 1: v ^= r
    if v == 0: return 0
    p = v.bit_length() - 1
    for q in list(piv):
        if (piv[q] >> p) & 1: piv[q] ^= v
    piv[p] = v; return v
def reduce(piv, v):
    for p, r in piv.items():
        if (v >> p) & 1: v ^= r
    return v
def solve_combo(vecs, target):
    """find c (bitmask over vecs) with sum c_i vecs[i] = target; returns (c or None, kernel basis)"""
    piv = {}; comb = {}
    ker = []
    for i, v in enumerate(vecs):
        c = 1 << i
        for p in sorted(piv, reverse=True):
            if (v >> p) & 1: v ^= piv[p]; c ^= comb[p]
        if v == 0: ker.append(c)
        else: p = v.bit_length() - 1; piv[p] = v; comb[p] = c
    t = target; c = 0
    for p in sorted(piv, reverse=True):
        if (t >> p) & 1: t ^= piv[p]; c ^= comb[p]
    return (c if t == 0 else None), ker
def affine_solutions(eqs, m):
    """eqs: list of (mask, rhs) over F2^m; returns list of all solutions w (or [] )"""
    piv = {}
    for mask, rhs in eqs:
        v = mask | (rhs << m)
        for p, r in piv.items():
            if (v >> p) & 1: v ^= r
        if v & ((1 << m) - 1) == 0:
            if v: return []
            continue
        p = (v & ((1 << m) - 1)).bit_length() - 1
        for q in list(piv):
            if (piv[q] >> p) & 1: piv[q] ^= v
        piv[p] = v
    free = [j for j in range(m) if j not in piv]
    sols = []
    for bits in range(1 << len(free)):
        w = 0
        for k, j in enumerate(free):
            if (bits >> k) & 1: w |= 1 << j
        for p, r in piv.items():
            val = (r >> m) & 1
            val ^= bin(r & w & ((1 << m) - 1) & ~(1 << p)).count('1') & 1
            if val: w |= 1 << p
        sols.append(w)
    return sols
def colvec(Y, mask):
    return np.bitwise_xor.reduce(Y[:, [j for j in range(Y.shape[1]) if (mask >> j) & 1]], axis=1) if mask else np.zeros(len(Y), np.uint8)
def tobig(bits):
    return int.from_bytes(np.packbits(bits.astype(np.uint8), bitorder='little').tobytes(), 'little')
stats = {'nodes': 0, 'cand': 0}
def level(Yb, Pb, m, K, path, abbin, out, nmax):
    """Yb: N x m uint8 (hull coords of current D), Pb: list of big ints (outputs)"""
    stats['nodes'] += 1
    N = Yb.shape[0]; ONE = (1 << N) - 1
    Ys = [tobig(Yb[:, j]) for j in range(m)]
    piv = {}; rref_add(piv, ONE)
    for y in Ys: rref_add(piv, y)
    dV = len(piv)
    for p in Pb: rref_add(piv, p)
    r = len(piv) - dV
    if r == 0: out.append(list(path)); return True
    if r > K: return False
    if r < K and not path: out.append(['ROOT-SLACK', r])
    pairs = [(i, j) for i in range(m) for j in range(i + 1, m)]
    red = [reduce(piv, Ys[i] & Ys[j]) for i, j in pairs]
    p2 = {}
    for v in red: rref_add(p2, v)
    pk = sorted(p2); rho = len(pk)
    inp = '%d %d\n' % (m, rho) + ''.join(''.join('1' if (v >> p) & 1 else '0' for p in pk) + '\n' for v in red) if rho else None
    if rho == 0: lines = [' '.join(map(str, [a] + [1 << j for j in range(m)])) for a in range(1, 1 << m)]
    else: lines = subprocess.run([abbin], input=inp, capture_output=True, text=True, check=True).stdout.split('\n')
    subs = set()
    for ln in lines:
        if not ln: continue
        xs = list(map(int, ln.split())); a = xs[0]; ker = xs[1:]
        # all b in span(ker) not in {0, a}
        for bits in range(1, 1 << len(ker)):
            b = 0
            for k in range(len(ker)):
                if (bits >> k) & 1: b ^= ker[k]
            if b == a or b == 0: continue
            subs.add(tuple(sorted((a, b, a ^ b))))
    # C0 / c0 machinery: vecs = Y_j, then 1, P_j
    base = Ys + [ONE] + list(Pb)
    _, ker0 = solve_combo(base, 0)
    C0 = [k & ((1 << m) - 1) for k in ker0]
    Vpiv = {}; rref_add(Vpiv, ONE); [rref_add(Vpiv, y) for y in Ys]
    found = False
    for (a, b, _), al, be in itertools.product(subs, (0, 1), (0, 1)):
        # a, b are affine: the 4 constant choices give the 4 point-indicators of span{a,b} (bases are equivalent)
        av = colvec(Yb, a) ^ al; bv = colvec(Yb, b) ^ be; f = av & bv
        AB = tobig(f)
        if reduce(Vpiv, AB) == 0: continue  # ab affine on D: no-op gate
        c, _ = solve_combo(base, AB)
        if c is None: continue  # (should not happen: ab in W)
        c0 = c & ((1 << m) - 1)
        eqs = [(cc, 0) for cc in C0] + [(c0, 1), (a, 0), (b, 0)]
        if m < nmax:
            # case B: target w outside the linear hull of D.  Then span{1, Y_j + w_j ab} picks up ab itself, so the rank
            # always drops by one; all such w are equivalent under affine maps fixing D, so take a fresh coordinate.
            stats['cand'] += 1
            Y2 = np.concatenate([Yb, f[:, None]], axis=1)
            path.append((a, al, b, be, 'new'))
            if level(Y2, Pb, m + 1, K - 1, path, abbin, out, nmax): path.pop(); return True
            path.pop()
        for w in affine_solutions(eqs, m):
            stats['cand'] += 1
            wb = np.array([(w >> j) & 1 for j in range(m)], np.uint8)
            Y2 = Yb ^ (f[:, None] * wb[None, :])
            path.append((a, al, b, be, w))
            if level(Y2, Pb, m, K - 1, path, abbin, out, nmax): path.pop(); return True
            path.pop()
    return False
def hull(Dx, n):
    """affine-hull coordinates of the points Dx (ints over n bits): returns N x m uint8"""
    X = np.array([[(x >> j) & 1 for j in range(n)] for x in Dx], np.uint8)
    d0 = X[0]; Z = X ^ d0
    # basis of row space of Z
    rows = [tobig(Z[:, j]) for j in range(n)]  # columns as functions; pick independent coordinate functions
    piv = {}; keep = []
    ONE = (1 << len(Dx)) - 1
    for j in range(n):
        if rref_add(piv, rows[j]): keep.append(j)
    # coordinates y = Z[:, keep] are independent linear functions on D; every x_j is affine in them
    return Z[:, keep], keep
def run(perm, n, Dx, K, abbin):
    Y, keep = hull(Dx, n); m = Y.shape[1]
    Pv = np.asarray(perm, np.int64)[np.asarray(Dx)]
    Pb = [tobig(((Pv >> j) & 1).astype(np.uint8)) for j in range(n)]
    out = []; stats['nodes'] = 0; stats['cand'] = 0
    level(Y, Pb, m, K, [], abbin, out, n)
    return m, [o for o in out if o and o[0] != 'ROOT-SLACK'], [o for o in out if o and o[0] == 'ROOT-SLACK']
if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        sys.path.insert(0, __file__.rsplit('/', 1)[0])
        from block_peel import rand_circ
        abbin = sys.argv[2]; n, K, seed, tr = map(int, sys.argv[3:7]); rng = random.Random(seed)
        for t in range(tr):
            T = rand_circ(n, K, rng)
            m, h, sl = run(T, n, list(range(1 << n)), K, abbin); n1 = stats['nodes']
            m, h2, sl2 = run(T, n, list(range(1 << n)), K - 1, abbin)
            print('planted n', n, 'K', K, 'HIT' if h else ('ROOT-SLACK' if sl else 'MISS'), 'nodes', n1,
                  '| K-1:', 'HIT' if h2 else ('ROOT-SLACK' if sl2 else 'NONE'), flush=True)
        sys.exit()
    abbin = sys.argv[1]; blocks = json.load(open(sys.argv[2])); bi = int(sys.argv[3]); K = int(sys.argv[4])
    reach = [json.load(open(f)) for f in sys.argv[5:]]
    b = blocks[bi]; n = len(b['W'])
    Dx = sorted(set().union(*[set(rr[bi]['reach']) for rr in reach])) if reach else list(range(1 << n))
    m, h, sl = run(b['perm'] if 'perm' in b else None, n, Dx, K, abbin) if 'perm' in b else (None, None, None)
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b['tof'], 'K', K, '|D|', len(Dx), 'hull', m,
          'nodes', stats['nodes'], 'cand', stats['cand'], 'HIT ' + str(h[0]) if h else ('ROOT-SLACK' if sl else 'NONE(exact)'), flush=True)
