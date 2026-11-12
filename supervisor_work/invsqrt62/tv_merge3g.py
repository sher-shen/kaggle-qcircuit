# Supervisor 2026-11-12 04:4x UTC. Exact 3->2 test, NON-adjacent pairs, transvection model.
# Drop gate i; in the rest, replace gates j < k (gates strictly between them = M_c, fixed, case-dependent linear map) by new
# transvections Tj, Tk.  With X_c = prefix state, Y_c = state required right after k (suffix^-1(end)) and Tk an involution:
#   M_c Tj X_c = Tk Y_c  <=>  X_c ^ M_c^-1 Y_c = a vj ^ b u_c,   a = [j active] <Lj,X_c>,  b = [k active] <Lk,Y_c>,  u_c = M_c^-1 vk
# (using <Lk,vk> = 0).  Everything is linear in (Lj, Lk) once fj, fk, vj, vk are fixed; vj/vk are pinned by the single-active
# classes or enumerated from the span of a both-active case (rank 2 preferred).  Incomplete only when neither pins them.
# Usage: python3 tv_merge3g.py in_tv.txt gates.txt [selftest]
import sys
exec(open(__file__.replace('tv_merge3g.py', 'tv_merge3.py')).read().split("def pair_solutions")[0])
def vapply(net, cm, u, inverse=False):  # apply gates to a wire-space vector u (bits = wire values)
    for g in (reversed(net) if inverse else net):
        L, v, f = g
        if par(f & cm) and par(L & u): u ^= v
    return u
def gen_solutions(pre, mid, post, first_only=True):
    info = []
    for cm, st, en in cases:
        X = run(pre, cm, st); Y = list(en)
        for g in reversed(post): Y = ap(Y, g, cm)
        Yp = list(Y)
        for g in reversed(mid): Yp = ap(Yp, g, cm)  # M^-1 Y (involutions)
        D = [x ^ y for x, y in zip(X, Yp)]
        info.append((cm, X, Y, D, span_basis(cols(D))))
    if any(len(b) > 2 for *_, b in info): return []
    nz = [i for i, c in enumerate(info) if c[4]]; sols = []
    for fj in range(1, NF + 1):
        aj = [par(fj & c[0]) for c in info]
        for fk in range(1, NF + 1):
            ak = [par(fk & c[0]) for c in info]
            if any(not (aj[i] or ak[i]) or (len(info[i][4]) == 2 and not (aj[i] and ak[i])) for i in nz): continue
            Jv = {info[i][4][0] for i in nz if aj[i] and not ak[i]}
            Kv = {vapply(mid, info[i][0], info[i][4][0]) for i in nz if ak[i] and not aj[i]}
            if len(Jv) > 1 or len(Kv) > 1: continue
            both = [i for i in nz if aj[i] and ak[i]]; both.sort(key=lambda i: -len(info[i][4]))
            if Jv: cj = list(Jv)
            elif both: cj = span_elems(info[both[0]][4])
            else: cj = [None]
            if Kv: ck = list(Kv)
            elif both: ck = [vapply(mid, info[both[0]][0], u) for u in span_elems(info[both[0]][4])]
            else: ck = [None]
            for vj in cj:
                for vk in ck:
                    if vj is None or vk is None: continue  # a gate that is never needed: a 2->1, covered elsewhere
                    eqs = [vec_eq(0, vj, 0), vec_eq(W, vk, 0)]; bad = False
                    for i, (cm, X, Y, D, b) in enumerate(info):
                        if not (aj[i] or ak[i]): continue
                        u = vapply(mid, cm, vk, inverse=True)
                        if aj[i] and ak[i]:
                            if not b: a_, b_ = 0, 0
                            else:
                                r = decomp(D, vj, u)
                                if r is None: bad = True; break
                                a_, b_ = r
                            eqs += formeq(0, X, a_) + formeq(W, Y, b_)
                        elif aj[i]:
                            r = 0 if not b else D[next(w for w in range(W) if vj >> w & 1)]
                            if b and any(D[w] != (r if vj >> w & 1 else 0) for w in range(W)): bad = True; break
                            eqs += formeq(0, X, r)
                        else:
                            r = 0 if not b else D[next(w for w in range(W) if u >> w & 1)]
                            if b and any(D[w] != (r if u >> w & 1 else 0) for w in range(W)): bad = True; break
                            eqs += formeq(W, Y, r)
                    if bad: continue
                    x = solve(eqs, 2 * W)
                    if x is None: continue
                    sols.append(((x & ((1 << W) - 1), vj, fj), (x >> W, vk, fk)))
                    if first_only: return sols
    return sols
def check(net):
    return all(run(net, cm, st) == list(en) for cm, st, en in cases)
K = len(G)
if len(sys.argv) > 3 and sys.argv[3] == 'selftest':
    miss = 0; tot = 0
    for j in range(K):
        for k in range(j + 1, min(K, j + 8)):
            tot += 1; s = gen_solutions(G[:j], G[j + 1:k], G[k + 1:])
            if not s: miss += 1; continue
            net = G[:j] + [s[0][0]] + G[j + 1:k] + [s[0][1]] + G[k + 1:]; assert check(net)
    print('selftest gap<=7 pairs', tot, 'miss', miss); sys.exit()
print('K', K, 'gates; exact 3->2: drop i, re-solve any pair j<k of the rest', flush=True)
found = 0
for i in range(K):
    rest = G[:i] + G[i + 1:]
    for j in range(len(rest)):
        for k in range(j + 1, len(rest)):
            s = gen_solutions(rest[:j], rest[j + 1:k], rest[k + 1:])
            if s:
                net = rest[:j] + [s[0][0]] + rest[j + 1:k] + [s[0][1]] + rest[k + 1:]; assert check(net)
                found += 1; print('MERGE drop', i, 'pair', j, k, flush=True)
                with open(sys.argv[2] + f'.m3g_{i}_{j}_{k}.txt', 'w') as fo:
                    for L, v, f in net: fo.write(f'{hex(L)} {hex(v)} {f}\n')
    print('i', i, 'found', found, flush=True)
print('found', found)
