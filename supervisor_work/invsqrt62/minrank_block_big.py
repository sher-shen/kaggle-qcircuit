"""Exact rank<=2 block search for blocks wider than 64 vertices (supervisor 2026-11-10 04 UTC, instruction 3 of 03:50).
Same algorithm and input as minrank_block.c (the .txt written by `MR_NOC=1 minrank_block.py dump.npz [--plant]`), but with
Python big ints so s is unlimited.  Used on the 14 phase-tap pairs (block 93..). Tree is tiny there (dense equations).
Usage: minrank_block_big.py dump.npz.txt [node_limit]"""
import sys
f = open(sys.argv[1]); s, ne = map(int, f.readline().split()); LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
lev, rhs, C = [], [], []
for _ in range(ne):
    v = list(map(int, f.readline().split())); lev.append(v[0]); rhs.append(v[1]); C.append(v[2:])
start = [0] * (s + 2); e = 0
for m in range(s + 2):
    while e < ne and lev[e] < m: e += 1
    start[m] = e
def spread(x, odd):
    r = 0; b = 0
    while x:
        if x & 1: r |= 1 << (2 * b + odd)
        x >>= 1; b += 1
    return r
nodes = 0; found = []; U = [0] * s; W = [0] * s; dn = [0] * (s + 1)
def insert(bs, r, c):
    while r:
        h = r.bit_length() - 1
        if h not in bs: bs[h] = (r, c); return True
        rr, cc = bs[h]; r ^= rr; c ^= cc
    return c == 0
def dfs(m, bs, hasU, hasW):
    global nodes
    nodes += 1; dn[m] += 1
    if LIMIT and nodes > LIMIT: return
    K = (1 << m) - 1; wK = sum(1 << a for a in range(m) if W[a])
    for e in range(start[m], start[m + 1]):
        su = 0; sw = 0; Ce = C[e]
        for a in range(m):
            if U[a]: su ^= Ce[a]
            if W[a]: sw ^= Ce[a]
        c = (bin(su & wK).count('1') & 1) ^ rhs[e]
        if not insert(bs, spread(su & ~K, 0) | spread(sw & ~K, 1), c): return
    if m == s:
        if hasU and hasW: found.append((''.join(map(str, U)), ''.join(map(str, W))))
        return
    if not hasU: ch = [(0, 0), (1, 0)]
    elif not hasW: ch = [(0, 0), (1, 0), (0, 1)]
    else: ch = [(0, 0), (1, 0), (0, 1), (1, 1)]
    mask = ~(3 << (2 * m))
    for um, wm in ch:
        U[m] = um; W[m] = wm; nb = {}; ok = True
        for h, (r, c) in bs.items():
            a = (r >> (2 * m)) & 1; b = (r >> (2 * m + 1)) & 1; c ^= (a & wm) ^ (b & um); r &= mask
            if not r:
                if c: ok = False; break
                continue
            nb[r.bit_length() - 1] = (r, c)
        if ok: dfs(m + 1, nb, hasU or um, hasW or wm)
        if len(found) > 3: return
    U[m] = W[m] = 0
sys.setrecursionlimit(10000)
dfs(0, {}, 0, 0)
print('nodes by depth', dn, file=sys.stderr)
for u, w in found[:3]: print('SOLUTION u=' + u, 'w=' + w)
print(f"RESULT {'HIT' if found else 'NONE(exact)'}{' [LIMIT HIT - NOT EXACT]' if LIMIT and nodes > LIMIT else ''} s={s} ne={ne} nodes={nodes} solutions={len(found)}")
