"""Non-greedy block extraction + residue-rank bound (instruction 2 of SUPERVISOR 11-10 22:55).
Same block definition as block_extract.py (wire set W, every op touching W in the interval is a classical permutation gate
inside W with the same condition context), but the growth branches: from every state W both blocking ops (before / after)
may be absorbed, giving a DAG of wire sets per seed (BFS, at most MAXST states per seed, |W| <= NMAX).
For every distinct op set the residue rank (block_rank.py, full domain) is computed with vectorised numpy / big-int GF(2)
elimination, so n up to ~20 is cheap.  rank == t closes t -> t-1 on the full domain; rank < t blocks are printed (OPEN).
Usage: block_extract2.py ops.json NMAX MAXST out.json"""
import json, sys, bisect
import numpy as np
from collections import Counter, deque
d = json.load(open(sys.argv[1])); NMAX = int(sys.argv[2]); MAXST = int(sys.argv[3]); K = d['kinds']; ops = d['ops']
PERM = {'X', 'CX', 'CCX', 'SWAP', 'CSWAP'}; TOF = {'CCX': 1, 'CSWAP': 1}
QARGS = {'X': 1, 'Z': 1, 'R': 1, 'CX': 2, 'CZ': 2, 'SWAP': 2, 'CCX': 3, 'CCZ': 3, 'CSWAP': 3, 'HMR': 1, 'Z_POW': 1}
stack = []; info = []
for o in ops:
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(o[1]); info.append((k, (), None)); continue
    if k == 'POP_CONDITION': stack.pop(); info.append((k, (), None)); continue
    nq = QARGS.get(k, 0); qs = tuple(o[1:1 + nq]); cond = o[1 + nq] if k != 'Z_POW' else o[2]
    info.append((k, qs, (tuple(stack), cond)))
by_wire = {}
for i, (k, qs, c) in enumerate(info):
    for q in qs: by_wire.setdefault(q, []).append(i)
def ok(i, W, ctx):
    k, qs, c = info[i]; return k in PERM and c == ctx and all(q in W for q in qs)
def interval(seed, W, ctx):
    lo = hi = seed; blo = bhi = None
    while True:
        prev = [L[a - 1] for q in W for L in [by_wire.get(q, [])] for a in [bisect.bisect_left(L, lo)] if a > 0]
        if not prev: break
        j = max(prev)
        if ok(j, W, ctx): lo = j
        else: blo = j; break
    while True:
        nxt = [L[a] for q in W for L in [by_wire.get(q, [])] for a in [bisect.bisect_right(L, hi)] if a < len(L)]
        if not nxt: break
        j = min(nxt)
        if ok(j, W, ctx): hi = j
        else: bhi = j; break
    sel = set()
    for q in W:
        L = by_wire.get(q, []); sel.update(L[bisect.bisect_left(L, lo):bisect.bisect_right(L, hi)])
    return tuple(sorted(sel)), blo, bhi
def perm_bits(W, sel):
    W = sorted(W); pos = {q: n for n, q in enumerate(W)}; n = len(W)
    y = np.arange(1 << n, dtype=np.uint32)
    for j in sel:
        k, qs, _ = info[j]; b = [pos[q] for q in qs]; g = lambda p: (y >> np.uint32(p)) & np.uint32(1)
        if k == 'X': y ^= np.uint32(1 << b[0])
        elif k == 'CX': y ^= g(b[0]) << np.uint32(b[1])
        elif k == 'CCX': y ^= (g(b[0]) & g(b[1])) << np.uint32(b[2])
        elif k == 'SWAP':
            m = g(b[0]) ^ g(b[1]); y ^= (m << np.uint32(b[0])) | (m << np.uint32(b[1]))
        elif k == 'CSWAP':
            m = g(b[0]) & (g(b[1]) ^ g(b[2])); y ^= (m << np.uint32(b[1])) | (m << np.uint32(b[2]))
    return n, y
def toint(bits):
    return int.from_bytes(np.packbits(bits.astype(np.uint8), bitorder='little').tobytes(), 'little')
def res_rank(n, y):
    x = np.arange(1 << n, dtype=np.uint32); piv = {}
    def add(r):
        while r:
            p = r.bit_length() - 1
            if p in piv: r ^= piv[p]
            else: piv[p] = r; return True
        return False
    add(toint(np.ones(1 << n, np.uint8)))
    for j in range(n): add(toint((x >> np.uint32(j)) & np.uint32(1)))
    return sum(add(toint((y >> np.uint32(j)) & np.uint32(1))) for j in range(n))
seen = {}; st = Counter(); opened = []
seeds = [i for i, (k, qs, c) in enumerate(info) if k in TOF]
for s in seeds:
    ctx = info[s][2]; W0 = frozenset(info[s][1]); Q = deque([W0]); vis = {W0}
    while Q and len(vis) <= MAXST:
        W = Q.popleft(); sel, blo, bhi = interval(s, W, ctx)
        t = sum(TOF.get(info[j][0], 0) for j in sel)
        if t >= 2 and sel not in seen:
            n, y = perm_bits(W, sel); r = res_rank(n, y); seen[sel] = (sorted(W), t, r)
            v = 'NONE' if r >= t else 'OPEN'
            st[(n, t, v)] += 1
            if r > t: print('BUG', sel[0], flush=True)
            if r < t: opened.append({'W': sorted(W), 'ops': list(sel), 'tof': t, 'rank': r}); print('OPEN n %d tof %d rank %d ops %d..%d' % (n, t, r, sel[0], sel[-1]), flush=True)
        for b in (blo, bhi):
            if b is None: continue
            k, qs, c = info[b]
            if k in PERM and c == ctx:
                W2 = W | frozenset(qs)
                if len(W2) <= NMAX and W2 not in vis: vis.add(W2); Q.append(W2)
json.dump(opened, open(sys.argv[4], 'w'))
for k in sorted(st): print('n %d tof %d %s: %d' % (k + (st[k],)))
print('distinct blocks', len(seen), 'open', len(opened))
