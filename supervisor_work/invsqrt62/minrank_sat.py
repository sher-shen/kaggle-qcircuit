"""SAT version of the MinRank rank<=2 test (supervisor 2026-11-08 23 UTC, instruction 1 of 22:40).
For pairs where k is too large for the linearisation (k > KMAX, ~350), decide exactly whether
  Q0 + sum_i l_i K_i  ==  u ^ w   (alternating rank <= 2, i.e. the quadratic part of (u.v)(w.v))
for some l in GF(2)^k, u, w in GF(2)^n.  Encoding for CryptoMiniSat: z_ab = u_a AND w_b (a != b, Tseitin),
and per index pair (a<b) one native XOR clause  z_ab + z_ba + sum_i E[t,i] l_i = E[t,0].
UNSAT => no affine g, h exist for ANY weight (sound, since K is a superset of the true relations).
SAT   => returns (u, w, l); the caller must re-validate with fresh samples (spurious relations make SAT easier).
Symmetry breaking: (u, w) -> GL2 orbit; we only require u != 0 lexicographic-free (no breaking, small n).
"""
import os, time
import numpy as np

def sat_test(E, pairs, n, timeout=None):
    import pycryptosat
    timeout = timeout or float(os.environ.get('MR_SAT_T', '600'))
    k = E.shape[1] - 1
    s = pycryptosat.Solver(threads=int(os.environ.get('MR_SAT_THREADS', '1')), time_limit=timeout)
    U = lambda a: 1 + a; W = lambda a: 1 + n + a; Lv = lambda i: 1 + 2 * n + i
    nxt = [1 + 2 * n + k]
    z = {}
    def Z(a, b):
        if (a, b) not in z:
            v = nxt[0]; nxt[0] += 1; z[(a, b)] = v
            s.add_clause([-v, U(a)]); s.add_clause([-v, W(b)]); s.add_clause([v, -U(a), -W(b)])
        return z[(a, b)]
    if os.environ.get('MR_SAT_SB', '1') == '1':
        # reduced row echelon form of the 2 x n matrix [u; w]: pivot(u) < pivot(w), w = 0 at pivot(u), u = 0 at pivot(w)
        def prefix(X):
            p = []
            for a in range(n):
                v = nxt[0]; nxt[0] += 1
                if a == 0: s.add_clause([-v, X(0)]); s.add_clause([v, -X(0)])
                else:
                    s.add_clause([-v, p[-1], X(a)]); s.add_clause([v, -X(a)]); s.add_clause([v, -p[-1]])
                p.append(v)
            return p
        pu = prefix(U); pw = prefix(W)
        s.add_clause([-W(0)])
        for a in range(1, n):
            s.add_clause([-W(a), pu[a - 1]])
            s.add_clause([-W(a), pw[a - 1], -U(a)])
    nx = 0
    for t, (a, b) in enumerate(pairs):
        vs = [Z(a, b), Z(b, a)] + [int(Lv(i)) for i in np.nonzero(E[t, 1:])[0]]
        s.add_xor_clause(vs, bool(E[t, 0])); nx += 1
    t0 = time.time()
    res, sol = s.solve()
    dt = time.time() - t0
    if res is None: return None, f'sat-timeout {dt:.0f}s xors={nx}'
    if not res: return False, f'sat-UNSAT {dt:.0f}s xors={nx}'
    u = np.array([bool(sol[U(a)]) for a in range(n)]); w = np.array([bool(sol[W(a)]) for a in range(n)])
    l = np.array([bool(sol[Lv(i)]) for i in range(k)])
    # self-check of the returned witness
    for t, (a, b) in enumerate(pairs):
        lhs = (u[a] & w[b]) ^ (u[b] & w[a]); rhs = E[t, 0] ^ (np.count_nonzero(E[t, 1:] & l) & 1)
        assert lhs == rhs, 'witness check failed'
    return (u, w, l), f'sat-SAT {dt:.0f}s xors={nx} |u|={u.sum()} |w|={w.sum()}'
