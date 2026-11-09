"""Exact rank<=2 test by echelon branch-and-prune (supervisor 2026-11-08 23 UTC, instruction 1 of 22:40).
Input: a MinRank dump (minrank_core MR_DUMP=prefix -> E, pairs, n): does  Q0 + span(K) contain u^w  (u, w in GF(2)^n)?
Observation on the open lookup_c / late_curvature_norm pairs: only ~36 of the 61 basis wires are touched by any relation,
so u^w is a complete 3-partite graph on the classes {u,w}=10/01/11 that must lie inside the touched entries; vertices outside
the touched block must be 00 (unless u^w = 0, tested separately).
Method: eliminate l -> equations c.(u^w) = c.Q0 for c in Ann(K) (dim = npair - k).  Write c as an alternating matrix C, then
c.(u^w) = u^T C w.  Assign (u_a, w_a) vertex by vertex in reduced-echelon form (GL2 symmetry removed); for the m assigned
vertices, the equations of Ann(K) supported on entries touching them are LINEAR in the unassigned (u_R, w_R): check that
linear system for consistency (exact pruning).  At the leaves every equation is checked.  Exhaustive => exact answer.
Usage: minrank_block.py dump.npz [--plant]   (--plant adds a random u^w to Q0 inside the block as a self-test)"""
import sys, os, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(sys.argv[1]); E = d['E'].astype(bool); P = [tuple(map(int, p)) for p in d['pairs']]; n = int(d['n'])
k = E.shape[1] - 1; npair = len(P); idx = {p: t for t, p in enumerate(P)}
rng = np.random.default_rng(int(os.environ.get('SEED', '1')))
touched = E[:, 1:].any(1)
deg = np.zeros(n, int)
for t in np.nonzero(touched)[0]: a, b = P[t]; deg[a] += 1; deg[b] += 1
blk = [a for a in range(n) if deg[a] > 0]
if '--plant' in sys.argv:
    u = np.zeros(n, bool); w = np.zeros(n, bool)
    for a in blk: u[a] = rng.random() < 0.5; w[a] = rng.random() < 0.5
    l = rng.random(k) < 0.5
    for t, (a, b) in enumerate(P):
        E[t, 0] = (u[a] & w[b]) ^ (u[b] & w[a]) ^ bool(np.count_nonzero(E[t, 1:] & l) & 1)
    print('planted |u|', u.sum(), '|w|', w.sum())
outside_q0 = [t for t in np.nonzero(E[:, 0])[0] if not touched[t]]
# entries outside the block: must be 0 in u^w except where Q0 forces (handled: outside Q0 entry -> need u^w there -> impossible
# unless that vertex in block; we simply include all vertices that touch a Q0 entry too)
for t in outside_q0:
    for a in P[t]:
        if a not in blk: blk.append(a)
blk = sorted(blk); s = len(blk); pos = {a: i for i, a in enumerate(blk)}
bp = [(a, b) for a in blk for b in blk if a < b]
# entries touching outside vertices: all must be 0 in E (else 'touched') -> u^w must vanish there -> outside vertices 00
# (or all nonzero vertices in one class -> u^w = 0).  Test u^w = 0: Q0 in span(K) ?
def rank(M):
    M = M.copy(); r = 0; R, C = M.shape
    for c in range(C):
        piv = np.nonzero(M[r:, c])[0]
        if len(piv) == 0: continue
        p = r + piv[0]; M[[r, p]] = M[[p, r]]
        rows = np.nonzero(M[:, c])[0]; rows = rows[rows != r]; M[rows] ^= M[r]; r += 1
        if r == R: break
    return r
rk = rank(E[:, 1:].T); rk0 = rank(E.T)
print(f'n={n} k={k} rankK={rk} block={s} Q0 in span(K): {rk0 == rk}')
if rk0 == rk: print('RESULT HIT (u^w = 0)'); sys.exit(0)
# Ann(K) restricted to block entries (entries outside the block are untouched and Q0=0 there -> equations u^w=0 there
# are automatically satisfied once outside vertices are 00)
Kb = np.array([E[idx[p], 1:] for p in bp]).T  # k x nb
nb = len(bp); q0 = np.array([E[idx[p], 0] for p in bp])
# nullspace of Kb (vectors c in GF(2)^nb with Kb c = 0)
def nullspace(M):
    M = M.copy(); R, C = M.shape; pivc = []; r = 0
    for c in range(C):
        piv = np.nonzero(M[r:, c])[0] if r < R else []
        if len(piv) == 0: continue
        p = r + piv[0]; M[[r, p]] = M[[p, r]]
        rows = np.nonzero(M[:, c])[0]; rows = rows[rows != r]; M[rows] ^= M[r]; pivc.append(c); r += 1
        if r == R: break
    free = [c for c in range(C) if c not in set(pivc)]; N = []
    for fc in free:
        v = np.zeros(C, bool); v[fc] = True
        for i, pc in enumerate(pivc):
            if M[i, fc]: v[pc] = True
        N.append(v)
    return np.array(N)
A = nullspace(Kb); print('equations (Ann K on block)', len(A))
# vertex order: greedy, pick next vertex maximising the number of equations that become linear
def nlin(order):
    inR = np.ones(s, bool); inR[[pos[a] for a in order]] = False
    cols = [t for t, (a, b) in enumerate(bp) if inR[pos[a]] and inR[pos[b]]]
    return len(A) - (rank(A[:, cols]) if cols else 0)
order = []
rest = list(blk)
# start with the vertices of largest 'class' influence: just greedy by nlin, on a sample of candidates
while rest:
    if len(order) < int(os.environ.get('NFIX', '6')): best = rest[0]
    else:
        cand = rest if len(rest) <= 40 else list(rng.choice(rest, 40, replace=False))
        best = max(cand, key=lambda a: nlin(order + [a]))
    order.append(best); rest.remove(best)
if os.environ.get('ROT'): r_ = int(os.environ['ROT']); order = order[r_:] + order[:r_]
if os.environ.get('ORDER') == 'auto2':
    q0v = sorted({a for t in np.nonzero(E[:, 0])[0] for a in P[t]} & set(blk))
    order = q0v + [a for a in reversed(order) if a not in q0v]
elif os.environ.get('ORDER'): order = [int(x) for x in os.environ['ORDER'].split(',')]; assert sorted(order) == blk
prof = [nlin(order[:m]) for m in range(s + 1)]
print('order', order); print('linear equations by depth', prof)
# echelon basis of A adapted to the order: equation level = first depth at which it is linear
opos = {a: i for i, a in enumerate(order)}
lvl_of_entry = np.array([min(opos[a], opos[b]) for (a, b) in bp])  # entry becomes 'known/linear' after vertex min assigned
# equation linear at depth m iff all its entries have min index < m  -> level(eq) = max over its entries of (min index)+1
# reduce A to minimise levels: sort columns by lvl descending and do row echelon
colord = np.argsort(-lvl_of_entry, kind='stable')
Ar = A[:, colord].copy(); R = len(Ar); r = 0
for c in range(Ar.shape[1]):
    piv = np.nonzero(Ar[r:, c])[0]
    if len(piv) == 0: continue
    p = r + piv[0]; Ar[[r, p]] = Ar[[p, r]]; rows = np.nonzero(Ar[:, c])[0]; rows = rows[rows != r]; Ar[rows] ^= Ar[r]; r += 1
    if r == R: break
A2 = np.zeros_like(A); A2[:, colord] = Ar
levels = [int(max(lvl_of_entry[np.nonzero(c)[0]]) + 1) for c in A2]
ordr = np.argsort(levels, kind='stable'); A2 = A2[ordr]; levels = [levels[i] for i in ordr]
print('equation levels histogram', np.bincount(levels).tolist())
# write the C input: s, neq, per eq: level, rhs, s row masks (in order coordinates)
outp = sys.argv[1] + ('.plant' if '--plant' in sys.argv else '') + '.txt'
with open(outp, 'w') as fh:
    fh.write(f'{s} {len(A2)}\n')
    for c, lv in zip(A2, levels):
        rows = [0] * s
        for t in np.nonzero(c)[0]:
            a, b = bp[t]; ia, ib = opos[a], opos[b]; rows[ia] |= 1 << ib; rows[ib] |= 1 << ia
        rhs = int(np.count_nonzero(c & q0) & 1)
        fh.write(f'{lv} {rhs} ' + ' '.join(str(x) for x in rows) + '\n')
if '--plant' in sys.argv:
    uo = [int(u[a]) for a in order]; wo = [int(w[a]) for a in order]
    bad = 0
    for c, lv in zip(A2, levels):
        v = 0
        for t in np.nonzero(c)[0]:
            a, b = bp[t]; v ^= (u[a] & w[b]) ^ (u[b] & w[a])
        if v != (np.count_nonzero(c & q0) & 1): bad += 1
    print('plant check: violated equations', bad, 'u', ''.join(map(str, uo)), 'w', ''.join(map(str, wo)))
if os.environ.get('MR_NOC'): sys.exit(0)
exe = os.path.join(os.environ.get('MR_BIN', '/tmp'), 'minrank_block_c')
src = os.path.join(HERE, 'minrank_block.c')
if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
    subprocess.check_call(['gcc', '-O3', '-march=native', '-o', exe, src])
r = subprocess.run([exe, outp] + ([os.environ['MR_LIMIT']] if os.environ.get('MR_LIMIT') else []), capture_output=True, text=True); print(r.stdout.strip()); print(r.stderr.strip())
