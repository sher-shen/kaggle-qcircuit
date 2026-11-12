# Supervisor 2026-11-11 23:xx UTC. Exact SAT: can normalize levels 44+45 (21 CSWAPs today) be done with K CSWAPs?
# Model: K slots, each a CSWAP on a pair of wires 0..21 whose control is an affine non-constant form of (r43,r44,r45)
# (realisable with free CX on wires 43..45). Per case the network must map the start classes to the end classes
# extracted by n4445_sat_extract.py (constants 'z'/'o' interchangeable, data tokens exact). Pure permutation model:
# no CX between data wires, no extra ANDs for non-linear controls.
# Usage: python3.13 n4445_sat.py cases.json K [timeout_s] [skip_case000]
import json, sys, itertools, time
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
cases = json.load(open(sys.argv[1])); K = int(sys.argv[2])
skip000 = len(sys.argv) > 4 and sys.argv[4] == '1'  # drop case 000 and complemented controls
TO = float(sys.argv[3]) if len(sys.argv) > 3 else 3600
W = 22; pairs = list(itertools.combinations(range(W), 2))
forms = [(f, cst) for f in range(1, 8) for cst in ((0, 1) if not skip000 else (0,))]  # f bitmask over (r43,r44,r45)
def fval(form, cs):
    f, cst = form; return (sum(((f >> i) & 1) * cs[i] for i in range(3)) + cst) & 1
pool = IDPool(); cl = []
def v(*a): return pool.id(a)
def exactly_one(lits):
    cl.extend(CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses)
for t in range(K):
    exactly_one([v('s', t, p) for p in range(len(pairs))])
    exactly_one([v('f', t, j) for j in range(len(forms))])
    for w in range(W):  # touched
        ps = [i for i, (a, b) in enumerate(pairs) if w in (a, b)]
        T = v('T', t, w)
        cl.append([-T] + [v('s', t, i) for i in ps])
        for i in ps: cl.append([T, -v('s', t, i)])
# symmetry breaking: consecutive slots on disjoint pairs with the same form commute -> require pair index increasing
SB = {}
for t in range(K - 1):
    for j in range(len(forms)):
        e = v('eq', t, j); cl.append([-v('f', t, j), -v('f', t + 1, j), e])
    # same-form indicator E_t
    E = v('E', t); cl.append([-E] + [v('eq', t, j) for j in range(len(forms))])
    for j in range(len(forms)): cl.append([-v('eq', t, j), v('f', t, j)]); cl.append([-v('eq', t, j), v('f', t + 1, j)])
    # if same form and disjoint pairs then idx(t) < idx(t+1): forbid (i1 at t, i2 at t+1) with i2 < i1, disjoint
    for i1, p1 in enumerate(pairs):
        bad = [i2 for i2, p2 in enumerate(pairs) if i2 < i1 and not set(p1) & set(p2)]
        if not bad: continue
        B = v('B', t, i1)  # some bad pair chosen at t+1 given i1
        cl.append([-B] + [v('s', t + 1, i2) for i2 in bad])
        for i2 in bad: cl.append([B, -v('s', t + 1, i2)])
        cl.append([-E, -v('s', t, i1), -B])
    # identical consecutive gates cancel: forbid
    for i in range(len(pairs)): cl.append([-E, -v('s', t, i), -v('s', t + 1, i)])
for ci, C in enumerate(cases):
    cs = C['case']
    if skip000 and cs == [0, 0, 0]: continue
    classes = sorted(set(C['start']))
    for t in range(K):
        A = v('a', ci, t)
        for j, fm in enumerate(forms):
            cl.append([-v('f', t, j), A if fval(fm, cs) else -A])
    def X(t, w, k): return v('x', ci, t, w, k)
    for w in range(W):
        for k in classes:
            cl.append([X(0, w, k) if C['start'][w] == k else -X(0, w, k)])
            cl.append([X(K, w, k) if C['end'][w] == k else -X(K, w, k)])
    for t in range(K):
        A = v('a', ci, t)
        for w in range(W):
            for k in classes:  # inactive or untouched: copy
                cl.append([A, -X(t, w, k), X(t + 1, w, k)]); cl.append([A, X(t, w, k), -X(t + 1, w, k)])
                cl.append([v('T', t, w), -X(t, w, k), X(t + 1, w, k)]); cl.append([v('T', t, w), X(t, w, k), -X(t + 1, w, k)])
        for i, (a, b) in enumerate(pairs):
            s = v('s', t, i)
            for k in classes:
                for s1 in (1, -1):
                    cl.append([-s, -A, -s1 * X(t, a, k), s1 * X(t + 1, b, k)])
                    cl.append([-s, -A, -s1 * X(t, b, k), s1 * X(t + 1, a, k)])
import os
if os.environ.get('PROG') == '1':  # redundant: wires not yet at their final class <= 2 * (active slots left), per case
    for ci, C in enumerate(cases):
        if skip000 and C['case'] == [0, 0, 0]: continue
        for t in range(K):
            lits = [-v('x', ci, t, w, C['end'][w]) for w in range(W)]
            for t2 in range(t, K):
                A = v('a', ci, t2); A2 = v('a2', ci, t2)
                cl.append([A, -A2]); cl.append([-A, A2])
                lits += [-A, -A2]
            cl.extend(CardEnc.atmost(lits=lits, bound=2 * (K - t), vpool=pool, encoding=EncType.seqcounter).clauses)
clean = cl
print('K', K, 'vars', pool.top, 'clauses', len(clean), flush=True)
t0 = time.time()
with Cadical153(bootstrap_with=clean) as S:
    import threading
    timer = threading.Timer(TO, lambda: S.interrupt()); timer.start()
    r = S.solve_limited(expect_interrupt=True); timer.cancel()
    print('result', {True: 'SAT', False: 'UNSAT', None: 'TIMEOUT'}[r], 'time %.1f' % (time.time() - t0), flush=True)
    if r:
        m = set(l for l in S.get_model() if l > 0)
        for t in range(K):
            p = [pairs[i] for i in range(len(pairs)) if v('s', t, i) in m][0]
            f = [forms[j] for j in range(len(forms)) if v('f', t, j) in m][0]
            print('slot', t, 'pair', p, 'form r43^r44^r45 mask', f[0], 'const', f[1])
