"""Chain-level (L -> L-1) Toffoli merge, witness search by SAT (supervisor 2026-11-09 00 UTC, instruction 1 of 00:15).
Input: dumps from chain_dump_scan.py (E, pairs, n; E[:,0] = Q0 = quadratic part of the chain sum F, E[:,1:] = relations K).
Question: is Q0 + span(K) hit by sum_{r<R} u_r ^ w_r  (alternating rank <= 2R), R = L-1 by default?  Then F = sum_r g_r h_r + affine,
i.e. the L CCX of the chain can be replaced by R = L-1 CCX at the last op.
l is eliminated (y = sum u_r^w_r + Q0 must satisfy the parity checks of span(K), K in reduced echelon form); CryptoMiniSat with
native XOR clauses.  SAT => witness (to be re-validated on fresh samples); UNSAT => proof; timeout => inconclusive.
Usage: rank4_sat.py [--R r] [--T seconds] [--plant] dump.npz ..."""
import sys, time, os, re, numpy as np, pycryptosat
args = sys.argv[1:]; R = None; T = 300.0; plant = False
while args and args[0].startswith('--'):
    o = args.pop(0)
    if o == '--R': R = int(args.pop(0))
    elif o == '--T': T = float(args.pop(0))
    elif o == '--plant': plant = True
rng = np.random.default_rng(3)
for fn in args:
    d = np.load(fn); E = d['E'].astype(bool); P = [tuple(map(int, p)) for p in d['pairs']]; n = int(d['n'])
    L = int(re.search(r'-L(\d+)_', fn).group(1)) if re.search(r'-L(\d+)_', fn) else 2
    RR = R or (L - 1); npair = len(P); k = E.shape[1] - 1
    if plant:  # replace Q0 by a random rank-2RR form + K l (on the touched vertices) as a self-test
        touched = E[:, 1:].any(1); vs = sorted({a for t in np.nonzero(touched)[0] for a in P[t]})
        y = np.zeros(npair, bool)
        for r in range(RR):
            u = np.zeros(n, bool); w = np.zeros(n, bool); u[vs] = rng.random(len(vs)) < .5; w[vs] = rng.random(len(vs)) < .5
            y ^= np.array([(u[a] & w[b]) ^ (u[b] & w[a]) for a, b in P])
        l = rng.random(k) < .5; E[:, 0] = y ^ ((E[:, 1:] & l).sum(1) & 1).astype(bool)
    t0 = time.time()
    Ki = [int(''.join('1' if x else '0' for x in E[::-1, 1 + i]), 2) for i in range(k)]
    Q0 = int(''.join('1' if x else '0' for x in E[::-1, 0]), 2)
    piv = {}
    for y in Ki:
        for p, v in piv.items():
            if (y >> p) & 1: y ^= v
        if not y: continue
        p = y.bit_length() - 1
        for q in list(piv):
            if (piv[q] >> p) & 1: piv[q] ^= y
        piv[p] = y
    s = pycryptosat.Solver(threads=1, time_limit=T)
    U = lambda r, a: 1 + 2 * r * n + a; W = lambda r, a: 1 + (2 * r + 1) * n + a
    nxt = [1 + 2 * RR * n]; ent = {}
    def AND(x, y):
        z = nxt[0]; nxt[0] += 1
        s.add_clause([-z, x]); s.add_clause([-z, y]); s.add_clause([z, -x, -y]); return z
    def entry(t):
        if t not in ent:
            c, dd = P[t]; ent[t] = [AND(U(r, c), W(r, dd)) for r in range(RR)] + [AND(U(r, dd), W(r, c)) for r in range(RR)]
        return ent[t]
    touch = {}
    for p, v in piv.items():
        v ^= 1 << p
        while v:
            e = v.bit_length() - 1; touch.setdefault(e, []).append(p); v ^= 1 << e
    pset = set(piv); ncl = 0
    for t in range(npair):
        if t in pset: continue
        vs = list(entry(t)); rhs = (Q0 >> t) & 1
        for p in touch.get(t, []): vs += entry(p); rhs ^= (Q0 >> p) & 1
        s.add_xor_clause(vs, bool(rhs)); ncl += 1
    sat, sol = s.solve(); dt = time.time() - t0
    res = 'UNSAT(exact)' if sat is False else ('TIMEOUT(inconclusive)' if sat is None else 'SAT-witness')
    extra = ''
    if sat:
        y = Q0
        for r in range(RR):
            u = [sol[U(r, a)] for a in range(n)]; w = [sol[W(r, a)] for a in range(n)]
            for t, (a, b) in enumerate(P):
                if (u[a] and w[b]) != (u[b] and w[a]): y ^= 1 << t
        for p, v in piv.items():
            if (y >> p) & 1: y ^= v
        extra = f' check_in_span={y == 0}'
    print(f'{os.path.basename(fn)} L={L} R={RR} n={n} k={k} rankK={len(piv)} xor={ncl} {res} {dt:.1f}s{extra}{" PLANT" if plant else ""}', flush=True)
