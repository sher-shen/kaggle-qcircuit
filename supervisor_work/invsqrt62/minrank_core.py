"""Exact pair test by MinRank (supervisor 2026-11-08 22 UTC, instruction 1 of 21:40).
Question for a same-target CCX pair: is f = p_i + p_j equal (on every sampled reachable state) to g*h + r with
g, h ARBITRARY affine functions of V_j (live wires at op j + recent bits) and r affine in V_j + V_end?
Write every degree<=2 function as  sum_{a<b} Q_ab v_a v_b + linear  over a basis v of V_j.  The representations of f form
Q0 + span(K_1..K_k) (K = the quadratic relations of the reachable states, from the samples; a superset of the true ones,
so a rejection is sound).  g*h has an alternating quadratic part of rank <= 2, and every rank<=2 alternating matrix is
u^w = quadratic part of (u.v)(w.v).  So: does B(l) = Q0 + sum l_i K_i have rank <= 2 for some l in GF(2)^k?
rank(B) <= 2  <=>  every 4x4 Pfaffian  B_ab B_cd + B_ac B_bd + B_ad B_bc = 0  (quadratic in l).
k <= EXH: enumerate all 2^k l (exact).  Otherwise linearise (unknowns 1, l_i, l_i l_j) and test consistency over random
4-subsets of the active indices: inconsistent => NO solution (proof); consistent => 'open' (could be spurious).
Returns (found, info)."""
import itertools, os
import numpy as np
EXH = int(os.environ.get('MR_EXH', '18')); KMAX = int(os.environ.get('MR_KMAX', '160'))
rng = np.random.default_rng(5)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')

def _basis_rows(rows):
    """greedy independent subset (indices) of bool rows, plus reduction basis"""
    basis = {}; keep = []
    for idx, v in enumerate(rows):
        x = toint(v)
        while x:
            p = x.bit_length() - 1
            if p in basis: x ^= basis[p]
            else: basis[p] = x; keep.append(idx); break
    return keep

def gf2_rank_bits(M):
    """M: (R, C) bool numpy -> rank, in place elimination on packed words"""
    R, C = M.shape
    W = np.packbits(M, axis=1, bitorder='little').view(np.uint8)
    W = np.ascontiguousarray(W)
    r = 0
    for c in range(C):
        byte, bit = c >> 3, np.uint8(1 << (c & 7))
        col = (W[r:, byte] & bit) != 0
        nz = np.nonzero(col)[0]
        if len(nz) == 0: continue
        p = r + nz[0]
        if p != r: W[[r, p]] = W[[p, r]]
        rows = np.nonzero((W[:, byte] & bit) != 0)[0]; rows = rows[rows != r]
        if len(rows): W[rows] ^= W[r]
        r += 1
        if r == R: break
    return r, W

def minrank(Vj, Vend, f, P=None):
    one = np.ones(len(f), bool)
    # distinct sample states
    ctr = list(P['ctr']) if P and 'ctr' in P else []
    allrows = np.concatenate([Vj, Vend, f[None]] + ([np.array(ctr)] if ctr else []), axis=0).T
    S = np.unique(allrows, axis=0)
    nj = len(Vj); ne = len(Vend); Sj = S[:, :nj]; Se = S[:, nj:nj + ne]; fs = S[:, nj + ne]; Sc = S[:, nj + ne + 1:]; M = len(S)
    r0 = len(_basis_rows([np.ones(M, bool)] + list(Sj.T)))
    cin = [Sc[:, c] for c in range(Sc.shape[1]) if len(_basis_rows([np.ones(M, bool)] + list(Sj.T) + [Sc[:, c]])) == r0]
    cand_rows = [np.ones(M, bool)] + cin + list(Sj.T)
    keep = _basis_rows(cand_rows)
    X = np.array([cand_rows[i] for i in keep if i > 0]).T; n = X.shape[1]
    def coords(v):
        """affine coordinates of v in (1, X) or None"""
        bas = {}; cmb = {}
        for ci, col in enumerate([np.ones(M, bool)] + list(X.T)):
            x_ = toint(col); c_ = 1 << ci
            while x_:
                p_ = x_.bit_length() - 1
                if p_ in bas: x_ ^= bas[p_]; c_ ^= cmb[p_]
                else: bas[p_] = x_; cmb[p_] = c_; break
        x_ = toint(v); c_ = 0
        while x_:
            p_ = x_.bit_length() - 1
            if p_ in bas: x_ ^= bas[p_]; c_ ^= cmb[p_]
            else: return None
        return [(c_ >> (t + 1)) & 1 for t in range(n)]
    Q0c = None
    if len(cin) == 4:
        u = [coords(c) for c in cin]
        if all(x is not None for x in u):
            Q0c = {}
            for g_, h_ in ((u[0], u[1]), (u[2], u[3])):
                for a_ in range(n):
                    for b_ in range(a_ + 1, n):
                        if (g_[a_] & h_[b_]) ^ (g_[b_] & h_[a_]): Q0c[(a_, b_)] = Q0c.get((a_, b_), 0) ^ 1
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
    lin = [np.ones(M, bool)] + list(X.T) + list(Se.T)
    lk = _basis_rows(lin); lin = [lin[i] for i in lk]; L = len(lin)
    cols = lin + [X[:, a] & X[:, b] for a, b in pairs]
    # column elimination with combination tracking
    basis = {}; comb = {}; kern = []
    for ci, v in enumerate(cols):
        x = toint(v); c = 1 << ci
        while x:
            p = x.bit_length() - 1
            if p in basis: x ^= basis[p]; c ^= comb[p]
            else: basis[p] = x; comb[p] = c; break
        if not x: kern.append(c)
    x = toint(fs); c = 0
    while x:
        p = x.bit_length() - 1
        if p in basis: x ^= basis[p]; c ^= comb[p]
        else: return None, f'notquad n={n}'
    qmask = lambda cc: cc >> L
    Q0 = qmask(c)
    if Q0c is not None:
        y = 0
        for t, pr in enumerate(pairs):
            if Q0c.get(pr): y |= 1 << t
        Q0alt = y
    else: Q0alt = None
    # independent Q-parts of the kernel
    Kb = {}; Ks = []
    for kk in kern:
        y = qmask(kk)
        while y:
            p = y.bit_length() - 1
            if p in Kb: y ^= Kb[p]
            else: Kb[p] = y; Ks.append(qmask(kk)); break
    k = len(Ks); npair = len(pairs)
    if Q0alt is not None:
        y = Q0alt ^ Q0
        while y:
            p_ = y.bit_length() - 1
            if p_ in Kb: y ^= Kb[p_]
            else: break
        if y == 0: Q0 = Q0alt
        else: print('WARN Q0alt not in coset', file=__import__('sys').stderr)
    def tomat(y):
        Bm = np.zeros((n, n), bool)
        for t in range(npair):
            if (y >> t) & 1: a, b = pairs[t]; Bm[a, b] = Bm[b, a] = True
        return Bm
    def rank2(Bm):
        return gf2_rank_bits(Bm.copy())[0] <= 2
    if rank2(tomat(Q0)): return ('rank<=2 at l=0',), f'n={n} k={k}'
    if k == 0: return None, f'n={n} k=0 exact'
    if k <= EXH:
        Kint = Ks
        # gray-code enumeration
        y = Q0
        for s in range(1, 1 << k):
            y ^= Kint[(s & -s).bit_length() - 1]
            if rank2(tomat(y)): return (f'l gray step {s}',), f'n={n} k={k} exh'
        return None, f'n={n} k={k} exact-exh'
    E = np.zeros((npair, k + 1), bool)
    for t in range(npair):
        E[t, 0] = (Q0 >> t) & 1
        for i in range(k): E[t, i + 1] = (Ks[i] >> t) & 1
    if os.environ.get('MR_DUMP') and k > KMAX:
        np.savez_compressed(os.environ['MR_DUMP'] + f"_{P.get('i', len(f)) if P else len(f)}_{k}.npz", E=E, pairs=np.array(pairs), n=n)
        return None, f'n={n} k={k} dumped'
    if os.environ.get('MR_SAT') == 'all' or (os.environ.get('MR_SAT') and k > KMAX):
        from minrank_sat import sat_test
        res, msg = sat_test(E, pairs, n)
        if res is False: return None, f'n={n} k={k} {msg}'
        if res is None: return ('sat timeout',), f'n={n} k={k} {msg}'
        u_, w_, l_ = res
        # g = u.v, h = w.v on the sample states; store for re-validation by the caller
        if P is not None: P['sat_gh'] = (X @ u_.astype(np.uint8) & 1, X @ w_.astype(np.uint8) & 1, S, nj, ne)
        return ('sat witness',), f'n={n} k={k} {msg}'
    if k <= KMAX:
        ok, msg = lin_test(E, pairs, n)
        return (None if not ok else ('linearised consistent',)), f'n={n} k={k} {msg}'
    # restricted necessary tests: principal submatrix on T must also have rank <= 2
    supp = sorted({x for t in range(npair) if E[t, 0] for x in pairs[t]})
    msgs = []
    for size in (len(supp), len(supp) + 4, len(supp) + 8, len(supp) + 12, len(supp) + 16, len(supp) + 24):
        for rep in range(3 if size > len(supp) else 1):
            extra = [x for x in rng.permutation(n) if x not in supp][:size - len(supp)]
            T = sorted(supp + extra); Ts = set(T)
            rt = [t for t in range(npair) if pairs[t][0] in Ts and pairs[t][1] in Ts]
            Et = E[rt]
            # independent parameter columns
            keepc = _basis_rows(list(Et[:, 1:].T)) if Et.shape[0] else []
            Et2 = np.concatenate([Et[:, :1], Et[:, 1:][:, keepc]], axis=1)
            kt = len(keepc)
            if kt > KMAX: msgs.append(f'T{len(T)}:kT{kt}>KMAX'); continue
            pt = [pairs[t] for t in rt]
            ok, msg = lin_test(Et2, pt, n)
            msgs.append(f'T{len(T)}:kT{kt}:' + msg.replace(' ', ','))
            if not ok: return None, f'n={n} k={k} REJECT-restricted ' + ' '.join(msgs)
    return ('restricted all consistent',), f'n={n} k={k} OPEN ' + ' '.join(msgs)

def lin_test(E, pairs, n):
    """E: rows = index pairs (a<b), col 0 = constant, cols 1.. = parameters. True if the linearised Pfaffian system is consistent."""
    k = E.shape[1] - 1; npair = len(pairs)
    if k == 0 or k <= EXH:
        # exhaustive (exact) on the restricted problem
        Bs = [E[:, c] for c in range(k + 1)]
        y = Bs[0].copy()
        def r2(y):
            Bm = np.zeros((n, n), bool)
            for t in np.nonzero(y)[0]: a_, b_ = pairs[t]; Bm[a_, b_] = Bm[b_, a_] = True
            return gf2_rank_bits(Bm)[0] <= 2
        if r2(y): return True, 'exh-found'
        for s_ in range(1, 1 << k):
            y ^= Bs[(s_ & -s_).bit_length()]
            if r2(y): return True, 'exh-found'
        return False, 'exh-none'
    idx = {p: t for t, p in enumerate(pairs)}
    act = sorted({a for t in range(npair) if E[t].any() for a in pairs[t]})
    nu = 1 + k + k * (k - 1) // 2
    iu = np.triu_indices(k, 1)
    def eq(a, b, c_, d_):
        tot = np.zeros(nu, bool)
        for (p1, p2), (p3, p4) in (((a, b), (c_, d_)), ((a, c_), (b, d_)), ((a, d_), (b, c_))):
            al = E[idx[(p1, p2)]]; be = E[idx[(p3, p4)]]
            if not al.any() or not be.any(): continue
            U = np.outer(al, be)
            tot[0] ^= U[0, 0]
            tot[1:k + 1] ^= U[0, 1:] ^ U[1:, 0] ^ np.diagonal(U)[1:]
            Uq = U[1:, 1:]
            tot[k + 1:] ^= (Uq ^ Uq.T)[iu]
        return tot
    R = min(4 * nu + 200, 120000)
    nzp = [pairs[t] for t in range(npair) if E[t].any()]
    subs = set(); order = rng.permutation(len(nzp) * len(nzp)) if len(nzp) ** 2 <= 4_000_000 else rng.integers(0, len(nzp) ** 2, 8 * R)
    for z in order:
        p1 = nzp[z // len(nzp)]; p2 = nzp[z % len(nzp)]
        s4 = set(p1) | set(p2)
        if len(s4) == 4: subs.add(tuple(sorted(s4)))
        if len(subs) >= R: break
    subs = list(subs); rows = []
    for s in subs:
        e = eq(*s)
        if e.any(): rows.append(e)
    if not rows: return True, 'noconstraint'
    A = np.array(rows)
    # consistency: rank(A[:,1:]) == rank(A)
    r1, _ = gf2_rank_bits(A[:, 1:].copy()); r2, _ = gf2_rank_bits(np.concatenate([A[:, 1:], A[:, :1]], axis=1))
    if r2 > r1: return False, f'lin-inconsistent rows={len(rows)} rank={r1}/{nu - 1}'
    return True, f'OPEN rows={len(rows)} rank={r1}/{nu - 1}'
