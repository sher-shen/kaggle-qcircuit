# Supervisor 2026-11-12 04:xx UTC. Exact 3->2 merge test in the transvection model (cswap_win_tv.c / tv_merge2.py).
# Drop gate i anywhere, and replace the adjacent pair (rest[p], rest[p+1]) of the remaining network by two new transvections
# T_k T_j (forms fj, fk; masks Lj, vj, Lk, vk; <Lj,vj> = <Lk,vk> = 0), all other gates fixed.  Per case D_c = X_c ^ Y_c with
# X_c the prefix state and Y_c = suffix^-1(end):
#   neither active: D_c = 0;  only j: D_c = vj (x) <Lj,X_c>;  only k: D_c = vk (x) <Lk,X_c>;
#   both: D_c = vj (x) a ^ vk (x) b,  a = <Lj,X_c>,  b = <Lk,X_c> ^ beta*a,  beta = <Lk,vj>.
# vj / vk are pinned by the rank-1 classes or enumerated in the span of the both-class column spaces; for each beta in {0,1}
# the rest is one GF(2) linear system over (Lj, Lk).  Exact for the enumerated v's (vj = vk is a 2->1 merge, tested by tv_merge2).
# Usage: python3 tv_merge3.py in_tv.txt gates.txt [selftest]
import sys, itertools
lines = open(sys.argv[1]).read().split('\n'); W, NCT, NC = map(int, lines[0].split()); NF = (1 << NCT) - 1; T = W + 1
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
def run(net, cm, st):
    s = list(st)
    for g in net: s = ap(s, g, cm)
    return s
import os
if os.environ.get('TV_NEARMISS') != '1':  # near-miss inputs (nearmiss_resolve.sh) are not exact by construction
    for cm, st, en in cases: assert run(G, cm, st) == list(en), 'network does not implement the window'
def cols(D):  # wire-space column vectors, one per form bit
    return [sum(1 << w for w in range(W) if D[w] >> t & 1) for t in range(T)]
def span_basis(vs):
    b = []
    for v in vs:
        for x in b:
            if v ^ x < v: v ^= x
        if v: b.append(v); b.sort(reverse=True)
    return b
def span_elems(b):
    out = [0]
    for x in b: out += [y ^ x for y in out]
    return [y for y in out if y]
def solve(eqs, n):
    piv = []
    for m, r in eqs:
        for pm, pr, pb in piv:
            if m >> pb & 1: m ^= pm; r ^= pr
        if m:
            pb = m.bit_length() - 1
            piv = [(pm ^ m, pr ^ r, b) if pm >> pb & 1 else (pm, pr, b) for pm, pr, b in piv]; piv.append((m, r, pb))
        elif r: return None
    x = 0
    for pm, pr, pb in piv:
        if pr: x |= 1 << pb
    return x
def formeq(Lvar_shift, X, rhs):  # sum_w L[w] X[w] = rhs as T scalar equations
    return [(sum(1 << (w + Lvar_shift) for w in range(W) if X[w] >> t & 1), rhs >> t & 1) for t in range(T)]
def vec_eq(shift, v, r):
    return (sum(1 << (w + shift) for w in range(W) if v >> w & 1), r)
def decomp(D, vj, vk):
    # D[w] = vj[w] a ^ vk[w] b; find two wires with independent (vj,vk) patterns
    pats = {}
    for w in range(W):
        p = (vj >> w & 1, vk >> w & 1)
        if p != (0, 0) and p not in pats: pats[p] = w
    if len(pats) < 2: return None
    (p1, w1), (p2, w2) = list(pats.items())[:2]
    # solve p1 . (a,b) = D[w1], p2 . (a,b) = D[w2]
    for a_sel in ((1, 0), (0, 1), (1, 1)):
        pass
    det = p1[0] * p2[1] ^ p1[1] * p2[0]
    if not det: return None
    # inverse over GF(2) of [[p1a p1b],[p2a p2b]]
    inv = [[p2[1], p1[1]], [p2[0], p1[0]]]
    a = (D[w1] if inv[0][0] else 0) ^ (D[w2] if inv[0][1] else 0)
    b = (D[w1] if inv[1][0] else 0) ^ (D[w2] if inv[1][1] else 0)
    for w in range(W):
        if D[w] != ((a if vj >> w & 1 else 0) ^ (b if vk >> w & 1 else 0)): return None
    return a, b
def pair_solutions(pre, post, first_only=True):
    info = []
    for cm, st, en in cases:
        X = run(pre, cm, st); Y = list(en)
        for g in reversed(post): Y = ap(Y, g, cm)
        D = [x ^ y for x, y in zip(X, Y)]
        b = span_basis(cols(D)); info.append((cm, X, D, b))
    if any(len(b) > 2 for _, _, _, b in info): return []
    nz = [i for i, c in enumerate(info) if c[3]]
    sols = []
    for fj in range(1, NF + 1):
        aj = [par(fj & c[0]) for c in info]
        for fk in range(1, NF + 1):
            ak = [par(fk & c[0]) for c in info]
            ok = True
            for i in nz:
                if not (aj[i] or ak[i]) or (len(info[i][3]) == 2 and not (aj[i] and ak[i])): ok = False; break
            if not ok: continue
            Jv = {info[i][3][0] for i in nz if aj[i] and not ak[i]}; Kv = {info[i][3][0] for i in nz if ak[i] and not aj[i]}
            if len(Jv) > 1 or len(Kv) > 1: continue
            Bspan = span_basis([x for i in nz if aj[i] and ak[i] for x in info[i][3]])
            if len(Bspan) > 2: continue
            cj = list(Jv) if Jv else None; ck = list(Kv) if Kv else None
            full = span_basis(Bspan + (cj or []) + (ck or []))
            if len(full) > 2: continue
            E = span_elems(full)
            for vj in (cj or E):
                for vk in (ck or E):
                    if vj == vk: continue
                    if any(span_basis([vj, vk] + [x]) != span_basis([vj, vk]) for x in Bspan): continue
                    base = [vec_eq(0, vj, 0), vec_eq(W, vk, 0)]; bad = False
                    for i, (cm, X, D, b) in enumerate(info):
                        if aj[i] and ak[i]:
                            if not b: ab = (0, 0)
                            else:
                                ab = decomp(D, vj, vk)
                                if ab is None: bad = True; break
                            info_ab = ab
                            base.append(('both', X, ab))
                        elif aj[i]:
                            r = 0 if not b else D[next(w for w in range(W) if vj >> w & 1)]
                            if b and any(D[w] != (r if vj >> w & 1 else 0) for w in range(W)): bad = True; break
                            base += formeq(0, X, r)
                        elif ak[i]:
                            r = 0 if not b else D[next(w for w in range(W) if vk >> w & 1)]
                            if b and any(D[w] != (r if vk >> w & 1 else 0) for w in range(W)): bad = True; break
                            base += formeq(W, X, r)
                    if bad: continue
                    for beta in (0, 1):
                        eqs = [vec_eq(W, vj, beta)]
                        for e in base:
                            if isinstance(e[0], str):
                                _, X, (a, bb) = e
                                eqs += formeq(0, X, a) + formeq(W, X, bb ^ (a if beta else 0))
                            else: eqs.append(e)
                        x = solve(eqs, 2 * W)
                        if x is None: continue
                        Lj, Lk = x & ((1 << W) - 1), x >> W
                        sols.append(((Lj, vj, fj), (Lk, vk, fk)))
                        if first_only: return sols
    return sols
def check(net):
    return all(run(net, cm, st) == list(en) for cm, st, en in cases)
K = len(G)
if len(sys.argv) > 3 and sys.argv[3] == 'selftest':
    # every adjacent pair of the original network must be re-found (dummy dropped gate)
    miss = 0
    for p in range(K - 1):
        s = pair_solutions(G[:p], G[p + 2:])
        if not s: miss += 1; print('selftest MISS pair', p)
        else:
            net = G[:p] + list(s[0]) + G[p + 2:]; assert check(net)
    print('selftest pairs', K - 1, 'miss', miss)
    # planted 3->2: insert x=(L1,v,f), y=(L2,v,f) (same v, <Li,v>=0) before gate p; x y = (L1^L2,v,f) is one gate, so
    # dropping x and re-solving (y, G[p]) must succeed.  Targets are recomputed for the planted network.
    import random; R = random.Random(1); hits = 0; tries = 0; orig = list(cases)
    while tries < 8:
        p = R.randrange(K); v = R.randrange(1, 1 << W); f = R.randrange(1, NF + 1)
        L1, L2 = R.randrange(1, 1 << W), R.randrange(1, 1 << W)
        if par(L1 & v) or par(L2 & v) or L1 == L2: continue
        net = G[:p] + [(L1, v, f), (L2, v, f)] + G[p:]
        cases[:] = [(cm, st, run(net, cm, st)) for cm, st, en in orig]
        if all(run(G, cm, st) == en for cm, st, en in cases): continue
        tries += 1
        s = pair_solutions(net[:p], net[p + 3:])
        if s and check(net[:p] + list(s[0]) + net[p + 3:]): hits += 1
    cases[:] = orig
    print('planted 3->2', tries, 'hit', hits); sys.exit()
print('K', K, 'gates; exact 3->2: drop i, re-solve adjacent pair p,p+1 of the rest', flush=True)
found = 0
for i in range(K):
    rest = G[:i] + G[i + 1:]
    for p in range(len(rest) - 1):
        s = pair_solutions(rest[:p], rest[p + 2:])
        if s:
            net = rest[:p] + list(s[0]) + rest[p + 2:]; assert check(net)
            found += 1; print('MERGE drop', i, 'pair', p, [(hex(L), hex(v), f) for L, v, f in s[0]], flush=True)
            with open(sys.argv[2] + f'.m3_{i}_{p}.txt', 'w') as fo:
                for L, v, f in net: fo.write(f'{hex(L)} {hex(v)} {f}\n')
    print('i', i, 'found', found, flush=True)
print('found', found)
