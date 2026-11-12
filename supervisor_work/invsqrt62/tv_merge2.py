# Supervisor 2026-11-12 03:xx UTC. Exact 2->1 merge test in the transvection model (cswap_win_tv.c).
# For a working network of K gates: remove gate i, and replace gate j (j != i) by the best single transvection (f, L, v)
# with all other gates fixed. Per case c with prefix state X_c and Y_c = suffix^-1(target) (transvections are involutions),
# D_c = X_c ^ Y_c must be 0 where f is inactive and = v (x) <L, X_c> where active: exact GF(2) linear algebra.
# Usage: python3 tv_merge2.py in_tv.txt gates.txt [drop_list]   gates: "a b form" (CSWAP) or "0xL 0xv form" lines, or "tv k 0xL 0xv f" logs
import sys, re
lines = open(sys.argv[1]).read().split('\n'); W, NCT, NC = map(int, lines[0].split()); NF = (1 << NCT) - 1
cases = []
for l in lines[1:1 + NC]:
    a = list(map(int, l.split())); cases.append((a[0], a[1:1 + W], a[1 + W:1 + 2 * W]))
G = []
for l in open(sys.argv[2]):
    t = l.split()
    if not t: continue
    if t[0] == 'tv': t = t[2:]
    if t[0].startswith('0x'): G.append((int(t[0], 16), int(t[1], 16), int(t[2])))
    else: m = (1 << int(t[0])) | (1 << int(t[1])); G.append((m, m, int(t[2])))
par = lambda x: bin(x).count('1') & 1
def ap(s, g, cm):
    L, v, f = g
    if not par(f & cm): return s
    a = 0
    for w in range(W):
        if L >> w & 1: a ^= s[w]
    if a: s = [s[w] ^ (a if v >> w & 1 else 0) for w in range(W)]
    return s
def solveL(eqs):  # eqs: list of (coef mask over W, rhs bit). returns (particular, nullspace basis) or None
    piv = []  # (mask, rhs, pivot bit)
    for m, r in eqs:
        for pm, pr, pb in piv:
            if m >> pb & 1: m ^= pm; r ^= pr
        if m: pb = m.bit_length() - 1; piv = [(pm ^ m, pr ^ r, b) if pm >> pb & 1 else (pm, pr, b) for pm, pr, b in piv]; piv.append((m, r, pb))
        elif r: return None
    x = 0
    for pm, pr, pb in piv:
        if pr: x |= 1 << pb
    pivs = {pb for _, _, pb in piv}; null = []
    for fr in range(W):
        if fr in pivs: continue
        z = 1 << fr
        for pm, pr, pb in piv:
            if pm >> fr & 1: z |= 1 << pb
        null.append(z)
    return x, null
def best_at(i, j):
    rest = [g for k, g in enumerate(G) if k != i]; jj = j if j < i else j - 1
    pre, post = rest[:jj], rest[jj + 1:]; D = []
    for cm, st, en in cases:
        X = list(st)
        for g in pre: X = ap(X, g, cm)
        Y = list(en)
        for g in reversed(post): Y = ap(Y, g, cm)
        D.append((cm, X, [x ^ y for x, y in zip(X, Y)]))
    sols = []
    for f in range(1, NF + 1):
        okf = True; v = None; eqs = []
        for cm, X, d in D:
            nz = [w for w in range(W) if d[w]]
            if not par(f & cm):
                if nz: okf = False; break
                continue
            if nz:
                r = d[nz[0]]
                if any(d[w] != r for w in nz): okf = False; break
                vm = sum(1 << w for w in nz)
                if v is None: v = vm
                elif v != vm: okf = False; break
            else: r = 0
            for t in range(W + 1):
                eqs.append((sum(1 << w for w in range(W) if X[w] >> t & 1), r >> t & 1))
        if not okf: continue
        if v is None: sols.append((i, j, 'identity', f)); continue
        s = solveL(eqs)
        if s is None: continue
        x, null = s
        cand = [x] + [x ^ z for z in null]
        for L in cand:
            if L and not par(L & v): sols.append((i, j, hex(L), hex(v), f)); break
    return sols
K = len(G); print('K', K, 'gates; checking all (drop i, re-solve j)')
found = 0
for i in range(K):
    for j in range(K):
        if j == i: continue
        for s in best_at(i, j): print('MERGE', s); found += 1
    sys.stdout.flush()
print('found', found)
