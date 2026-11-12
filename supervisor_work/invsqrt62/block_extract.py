"""Extract small pure-permutation blocks from ops.json (instruction 1 of SUPERVISOR 11-10 07:00).
Block = (wire set W, |W|<=NMAX, op interval [lo,hi]) such that every op in the interval touching W is a classical
permutation gate (X, CX, CCX, SWAP, CSWAP), lies entirely inside W, and has the same condition context; ops not touching
W commute with the block (disjoint wires).  The block's sub-sequence is then a permutation of 2^|W| states and could be
replaced by any other circuit for the same permutation.  Grown greedily from every CCX/CSWAP seed.
Output: JSON list of {W, ops:[op indices], tof, perm}.  Usage: block_extract.py ops.json NMAX out.json"""
import json, sys
d = json.load(open(sys.argv[1])); NMAX = int(sys.argv[2]); K = d['kinds']; ops = d['ops']
PERM = {'X': 1, 'CX': 2, 'CCX': 3, 'SWAP': 2, 'CSWAP': 3}
TOF = {'CCX': 1, 'CSWAP': 1}
QARGS = {'X': 1, 'Z': 1, 'R': 1, 'CX': 2, 'CZ': 2, 'SWAP': 2, 'CCX': 3, 'CCZ': 3, 'CSWAP': 3, 'HMR': 1, 'Z_POW': 1}
stack = []; info = []
for o in ops:
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(o[1]); info.append((k, (), None)); continue
    if k == 'POP_CONDITION': stack.pop(); info.append((k, (), None)); continue
    nq = QARGS.get(k, 0); qs = tuple(o[1:1 + nq])
    cond = o[1 + nq] if k != 'Z_POW' else o[2]
    info.append((k, qs, (tuple(stack), cond)))
by_wire = {}
for i, (k, qs, c) in enumerate(info):
    for q in qs: by_wire.setdefault(q, []).append(i)
import bisect
def ok(i, W, ctx):
    k, qs, c = info[i]
    return k in PERM and c == ctx and all(q in W for q in qs)
def touching(W, lo, hi):  # op indices in (lo,hi) touching W, sorted
    s = set()
    for q in W:
        L = by_wire.get(q, []); a = bisect.bisect_right(L, lo); b = bisect.bisect_left(L, hi)
        s.update(L[a:b])
    return sorted(s)
def grow(seed):
    W = set(info[seed][1]); ctx = info[seed][2]; out = []
    while True:
        # extend interval while ops touching W are ok
        lo = seed; hi = seed; blk_lo = blk_hi = None
        while True:  # backward
            prev = [i for q in W for i in by_wire.get(q, [])[:bisect.bisect_left(by_wire.get(q, []), lo)][-1:]]
            if not prev: break
            j = max(prev)
            if ok(j, W, ctx): lo = j
            else: blk_lo = j; break
        while True:  # forward
            nxt = [L[bisect.bisect_right(L, hi)] for q in W for L in [by_wire.get(q, [])] if bisect.bisect_right(L, hi) < len(L)]
            if not nxt: break
            j = min(nxt)
            if ok(j, W, ctx): hi = j
            else: blk_hi = j; break
        sel = [i for i in touching(W, lo - 1, hi + 1)]
        out.append((frozenset(W), tuple(sel)))
        # try to absorb a blocking op's wires
        grew = False
        for b in (blk_lo, blk_hi):
            if b is None: continue
            k, qs, c = info[b]
            if k in PERM and c == ctx and len(W | set(qs)) <= NMAX:
                W = W | set(qs); grew = True; break
        if not grew: return out
blocks = {}
for i, (k, qs, c) in enumerate(info):
    if k not in TOF: continue
    for W, sel in grow(i):
        t = sum(TOF.get(info[j][0], 0) for j in sel)
        if t >= 2: blocks[sel] = (W, t)
def perm(W, sel):
    W = sorted(W); pos = {q: n for n, q in enumerate(W)}; N = 1 << len(W); T = list(range(N))
    for x in range(N):
        y = x
        for j in sel:
            k, qs, _ = info[j]; b = [pos[q] for q in qs]; g = lambda p: (y >> p) & 1
            if k == 'X': y ^= 1 << b[0]
            elif k == 'CX': y ^= g(b[0]) << b[1]
            elif k == 'CCX': y ^= (g(b[0]) & g(b[1])) << b[2]
            elif k == 'SWAP':
                if g(b[0]) != g(b[1]): y ^= (1 << b[0]) | (1 << b[1])
            elif k == 'CSWAP':
                if g(b[0]) and g(b[1]) != g(b[2]): y ^= (1 << b[1]) | (1 << b[2])
        T[x] = y
    return W, T
# keep only maximal blocks (drop a block whose op set is a subset of another with same Toffoli count)
items = sorted(blocks.items(), key=lambda kv: -len(kv[0]))
res = []; sets = []
for sel, (W, t) in items:
    s = set(sel)
    if any(s <= S and t == tt for S, tt in sets): continue
    sets.append((s, t)); Ws, T = perm(W, sel)
    res.append({'W': Ws, 'ops': list(sel), 'tof': t, 'perm': T})
json.dump(res, open(sys.argv[3], 'w'))
from collections import Counter
print('blocks', len(res), Counter((len(r['W']), r['tof']) for r in res))
