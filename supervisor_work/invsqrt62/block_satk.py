"""Exact SAT test "P|D = (A g_K ... g_1)|D" for a block on n wires with reachable entry set D (don't-cares outside D).
g_j = affine conjugate of a Toffoli: s -> s ^ v [l1.s = c1 and l2.s = c2] (l1, l2, c1, c2, v free, l1.v = l2.v = 0),
A = any affine map at the end (invertibility NOT imposed: a relaxation, so UNSAT is an exact NONE; a SAT model is
re-checked in Python and A's rank is reported).  No ancilla (same model as dc3.c, but any K).
Usage: block_satk.py blocks.json idx ops.json K [solver]            (real block)
       block_satk.py --plant blocks.json idx K seed [solver]          (random planted K-gate circuit on the block's D)"""
import sys, json, random, time
from pysat.solvers import Solver
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from block_dc3 import sim
par = lambda v: bin(v).count('1') & 1

class Enc:
    def __init__(s): s.nv = 0; s.cl = []; s.T = None
    def new(s): s.nv += 1; return s.nv
    def const(s, b):
        if s.T is None: s.T = s.new(); s.cl.append([s.T])
        return s.T if b else -s.T
    def AND(s, a, b):
        if a is None or b is None: return None          # None = constant 0
        o = s.new(); s.cl += [[-o, a], [-o, b], [o, -a, -b]]; return o
    def XOR(s, a, b):
        if a is None: return b
        if b is None: return a
        o = s.new(); s.cl += [[-o, a, b], [-o, -a, -b], [o, -a, b], [o, a, -b]]; return o
    def XORL(s, xs):
        r = None
        for x in xs: r = s.XOR(r, x)
        return r
    def NOT(s, a): return s.const(1) if a is None else -a
    def eq(s, a, bit):  # literal a (or None=0) must equal constant bit
        if a is None:
            if bit: s.cl.append([])
            return
        s.cl.append([a] if bit else [-a])

def build(n, pts, K):
    e = Enc()
    G = []
    for j in range(K):
        g = {k: [e.new() for _ in range(n)] for k in ('l1', 'l2', 'v')}; g['c1'] = e.new(); g['c2'] = e.new(); G.append(g)
        for l in ('l1', 'l2'):  # l.v = 0
            e.eq(e.XORL([e.AND(a, b) for a, b in zip(g[l], g['v'])]), 0)
    A = [[e.new() for _ in range(n)] for _ in range(n)]; a0 = [e.new() for _ in range(n)]
    for x, px in pts:
        st = [e.const((x >> k) & 1) for k in range(n)]
        for g in G:
            u1 = e.NOT(e.XOR(e.XORL([e.AND(a, b) for a, b in zip(g['l1'], st)]), g['c1']))
            u2 = e.NOT(e.XOR(e.XORL([e.AND(a, b) for a, b in zip(g['l2'], st)]), g['c2']))
            f = e.AND(u1, u2)
            st = [e.XOR(sk, e.AND(f, vk)) for sk, vk in zip(st, g['v'])]
        for k in range(n):
            e.eq(e.XOR(e.XORL([e.AND(a, b) for a, b in zip(A[k], st)]), a0[k]), (px >> k) & 1)
    return e, G, A, a0

def solve(n, pts, K, sname='cadical195'):
    e, G, A, a0 = build(n, pts, K)
    t = time.time()
    with Solver(name=sname, bootstrap_with=e.cl) as S:
        ok = S.solve(); m = set(l for l in S.get_model() if l > 0) if ok else None
    dt = time.time() - t
    if not ok: return 'NONE(exact, UNSAT)', dt, e.nv, len(e.cl)
    val = lambda vs: sum(1 << i for i, v in enumerate(vs) if v in m)
    gs = [(val(g['l1']), val(g['l2']), int(g['c1'] in m), int(g['c2'] in m), val(g['v'])) for g in G]
    Ar = [val(r) for r in A]; c0 = val(a0)
    def run(x):
        for l1, l2, c1, c2, v in gs:
            if par(l1 & x) == c1 and par(l2 & x) == c2: x ^= v
        return sum(par(Ar[k] & x) << k for k in range(n)) ^ c0
    good = all(run(x) == px for x, px in pts)
    rows = Ar[:]; r = 0
    for c in range(n):
        p = next((i for i in range(r, n) if rows[i] >> c & 1), None)
        if p is None: continue
        rows[r], rows[p] = rows[p], rows[r]
        for i in range(n):
            if i != r and rows[i] >> c & 1: rows[i] ^= rows[r]
        r += 1
    return 'HIT(check %s, rank A %d) gates %s A %s a0 %d' % (good, r, gs, Ar, c0), dt, e.nv, len(e.cl)

if __name__ == '__main__':
    if sys.argv[1] == '--plant':
        bf, bi, K, seed = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); sname = sys.argv[6] if len(sys.argv) > 6 else 'cadical195'
        b = json.load(open(bf))[bi]; n = len(b['W']); S_ = 1 << n; rnd = random.Random(seed)
        gs = []
        while len(gs) < K:
            l1, l2 = rnd.randrange(1, S_), rnd.randrange(1, S_)
            if l1 == l2: continue
            vs = [v for v in range(1, S_) if not par(l1 & v) and not par(l2 & v)]
            gs.append((l1, l2, rnd.randrange(2), rnd.randrange(2), rnd.choice(vs)))
        def P(x):
            for l1, l2, c1, c2, v in gs:
                if par(l1 & x) == c1 and par(l2 & x) == c2: x ^= v
            return x
        res = solve(n, [(x, P(x)) for x in b['reach']], K, sname)
        print('plant seed', seed, 'block', bi, 'n', n, '|D|', len(b['reach']), 'K', K, res[0], 'time %.1fs vars %d clauses %d' % res[1:], flush=True)
        sys.exit()
    bf, bi, of, K = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]); sname = sys.argv[5] if len(sys.argv) > 5 else 'cadical195'
    d = json.load(open(of)); b = json.load(open(bf))[bi]; n = len(b['W'])
    pts = [(x, sim(b, d['ops'], d['kinds'], x)) for x in b['reach']]
    res = solve(n, pts, K, sname)
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b.get('tof'), '|D|', len(b['reach']), 'K', K, res[0],
          'time %.1fs vars %d clauses %d' % res[1:], flush=True)
