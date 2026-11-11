"""Exact necessary test for t -> 2 on the reachable set D of a block whose residue on D is a single function f (rank 1,
e.g. the 3-Toffoli inner-product blocks target ^= L1L2 + L3L4 + L5L6).
Any circuit with two AND/Toffoli gates (any width, any measurement-based uncompute, no borrowed dirty wire outside the
block) has outputs in span{1, y, u1, u2}, u1 = a1 b1, u2 = (al + s u1)(be + t u1), a1, b1, al, be affine on D.  Then
f = L + al be + g a1 b1 with g in span{1, al, be}, and in every case f is affine on each cell {h1 = c1, h2 = c2} of two affine
functions (h1, h2) = (al, a1), (al + be, a1) or (al, a1) -- i.e. on each coset of a codim-2 subspace Z = H^perp (hull coords).
Pruning: a violating 4-point affine dependency p+q+r+s = 0 in D with f(p)+f(q)+f(r)+f(s) = 1 can't lie in one coset, so
H must not be inside span{p+q, p+r}^perp (cells2.c enumerates all H).  Survivors get the exact per-cell affinity test.
Usage: block_cells2.py cells2_bin blocks.json idx [nproc] | --plant cells2_bin blocks.json idx kind seed"""
import sys, json, subprocess, random, itertools
import numpy as np
from collections import defaultdict
def hull(Dx, n):
    X = ((np.asarray(Dx)[:, None] >> np.arange(n)) & 1).astype(np.uint8)
    Z = X ^ X[0]; piv = {}; keep = []
    cols = [int.from_bytes(np.packbits(Z[:, j], bitorder='little').tobytes(), 'little') for j in range(n)]
    for j in range(n):
        v = cols[j]
        for p, r in piv.items():
            if (v >> p) & 1: v ^= r
        if v:
            p = v.bit_length() - 1
            for q in list(piv):
                if (piv[q] >> p) & 1: piv[q] ^= v
            piv[p] = v; keep.append(j)
    return Z[:, keep]
def residue(b, ops):
    """f on D for a block whose ops are CX / CCX into one target; returns f (uint8 per point)"""
    W = b['W']; n = len(W); pos = {q: i for i, q in enumerate(W)}
    X = ((np.asarray(b['reach'])[:, None] >> np.arange(n)) & 1).astype(np.uint8)
    lin = {q: 1 << pos[q] for q in W}; cst = {q: 0 for q in W}; f = np.zeros(len(X), np.uint8); tg = set()
    ev = lambda q: ((X & np.array([(lin[q] >> j) & 1 for j in range(n)], np.uint8)).sum(1) + cst[q]) & 1
    for i in b['ops']:
        o = ops[i]
        if o[0] == 1: lin[o[2]] ^= lin[o[1]]; cst[o[2]] ^= cst[o[1]]
        elif o[0] == 0: cst[o[1]] ^= 1
        elif o[0] == 2: f ^= (ev(o[1]) & ev(o[2])).astype(np.uint8); tg.add(o[3])
        else: raise SystemExit('unsupported op %s' % o)
        if tg and o[0] in (1, 2): assert not (set(o[1:-2] if o[0] == 2 else o[1:2]) & tg), 'target read'
    # the rest of the block is an affine map (not necessarily identity); residue on D = f in the single target
    assert len(tg) == 1, tg
    return f
def quads(Yi, f):
    buck = defaultdict(list)
    N = len(Yi)
    for p in range(N):
        for q in range(p + 1, N): buck[Yi[p] ^ Yi[q]].append((p, q))
    out = set()
    for v, pr in buck.items():
        for (p, q), (r, s) in itertools.combinations(pr, 2):
            if len({p, q, r, s}) < 4: continue
            if f[p] ^ f[q] ^ f[r] ^ f[s]:
                out.add(tuple(sorted(((Yi[p] ^ Yi[q]), (Yi[p] ^ Yi[r])))))
    return sorted(out)
def affine_on(Y, f, idx):
    if len(idx) <= 1: return True
    A = np.concatenate([np.ones((len(idx), 1), np.uint8), Y[idx], f[idx, None]], 1)
    def rk(M):
        M = M.copy(); r = 0
        for c in range(M.shape[1]):
            p = np.nonzero(M[r:, c])[0]
            if not len(p): continue
            p = p[0] + r; M[[r, p]] = M[[p, r]]
            rows = np.nonzero(M[:, c])[0]; rows = rows[rows != r]; M[rows] ^= M[r]; r += 1
            if r == M.shape[0]: break
        return r
    return rk(A) == rk(A[:, :-1])
def test(Y, f, cbin, nproc=4):
    m = Y.shape[1]; Yi = (Y.astype(np.int64) * (1 << np.arange(m))).sum(1).tolist()
    Q = quads(Yi, f)
    inp = '%d %d\n' % (m, len(Q)) + ''.join('%d %d\n' % q for q in Q)
    ps = [subprocess.Popen([cbin, str(k), str(nproc)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) for k in range(nproc)]
    for p in ps: p.stdin.write(inp); p.stdin.close()
    surv = []
    for p in ps: surv += [tuple(map(int, l.split())) for l in p.stdout.read().split('\n') if l]; p.wait()
    hits = []
    Yv = np.asarray(Yi)
    for h1, h2 in surv:
        c = (np.array([bin(v & h1).count('1') & 1 for v in Yi]) + 2 * np.array([bin(v & h2).count('1') & 1 for v in Yi]))
        if all(affine_on(Y, f, np.nonzero(c == k)[0]) for k in range(4)): hits.append((h1, h2))
    return len(Q), len(surv), hits
if __name__ == '__main__':
    if sys.argv[1] == '--plant':
        cbin, bf, bi, kind, seed = sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], int(sys.argv[6])
        b = json.load(open(bf))[bi]; n = len(b['W']); Y = hull(b['reach'], n); m = Y.shape[1]; rng = np.random.default_rng(seed)
        aff = lambda: (Y @ rng.integers(0, 2, m) + rng.integers(0, 2)) % 2
        L, al, be, a1, b1 = [aff().astype(np.uint8) for _ in range(5)]
        if kind == 'two': f = L ^ (al & be) ^ (a1 & b1)
        elif kind == 'nest': f = L ^ (al & (be ^ (a1 & b1)))
        else: f = L ^ (al & be) ^ (a1 & b1) ^ (aff().astype(np.uint8) & aff().astype(np.uint8))  # three products: should be NONE
        nq, ns, h = test(Y, f.astype(np.uint8), cbin)
        print('plant', kind, 'block', bi, 'm', m, 'viol quads', nq, 'survivors', ns, 'HIT' if h else 'NONE', h[:3], flush=True); sys.exit()
    cbin, bf, bi = sys.argv[1], sys.argv[2], int(sys.argv[3]); nproc = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    d = json.load(open(sys.argv[5] if len(sys.argv) > 5 else 'p62mm.json'))
    b = json.load(open(bf))[bi]; n = len(b['W']); Y = hull(b['reach'], n); f = residue(b, d['ops'])
    nq, ns, h = test(Y, f, cbin, nproc)
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b['tof'], '|D|', len(b['reach']), 'hull', Y.shape[1],
          'viol quads', nq, 'survivors', ns, ('HIT %s' % h[:3]) if h else 'NONE(exact, t->2)', flush=True)
