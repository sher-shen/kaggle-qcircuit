"""General-affine-factor test for same-target CCX pairs (supervisor 2026-11-08 06 UTC, instruction 1 of 05:25).
For f = p_i + p_j (two CCX into one target t) to be replaceable by ONE product g*h (+ affine r) with g, h ARBITRARY affine
combinations of the live wires at op j, the quadratic form of f must drop rank modulo the quadratic relations satisfied by
the reachable states.  If the live wires at op j satisfy NO quadratic relation beyond linear ones, the GF(2) quadratic form
of f in the live wires is unique modulo affine terms, and its symplectic rank (computed formally by stage_qform) is final.
This script samples the reachable states (every x repeated REPS times for HMR histories) at each candidate pair's op j and
computes the dimension of the space of polynomials of degree <= 2 in the live wires that vanish on all samples
(= #monomials - rank).  It reports the linear relations and the genuinely quadratic ones separately.
Usage: quad_rel_scan.py ops.json [nsample] [reps] [maxgap]"""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 8; MAXGAP = int(sys.argv[4]) if len(sys.argv) > 4 else 60
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(11)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
QA = {'CX': 2, 'CCX': 3, 'CSWAP': 3, 'SWAP': 2, 'X': 1, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'HMR': 1, 'R': 1, 'Z_POW': 1, 'S': 1, 'T': 1}
cand = {}
for i, o in enumerate(ops):
    if K[o[0]] != 'CCX': continue
    t = o[3]
    for j in range(i + 1, min(len(ops), i + MAXGAP)):
        kj = K[ops[j][0]]; aj = ops[j][1:]
        if kj in ('PUSH_CONDITION', 'POP_CONDITION', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'NEG'): continue
        qa = aj[:QA.get(kj, 0)]
        if t not in qa: continue
        if kj == 'CCX' and aj[2] == t and t not in aj[:2]: cand[j] = i; break
        if kj == 'CX' and aj[1] == t: continue
        if kj == 'X': continue
        break
print('candidate pairs', len(cand), file=sys.stderr, flush=True)
def rank_rows(rows):
    basis = {}; r = 0
    for v in rows:
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; r += 1; break
    return r
def analyse(i, j, snap, t):
    live = [w for w in range(nq) if snap[w].any() and w != t]
    S = np.unique(snap[live].T, axis=0)            # distinct reachable states (t excluded)
    ns_ = len(S); toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
    one = np.ones(ns_, bool)
    lin = [toint(one)] + [toint(S[:, a]) for a in range(len(live))]
    rl = rank_rows(lin)
    quad = lin + [toint(S[:, a] & S[:, b]) for a in range(len(live)) for b in range(a + 1, len(live))]
    rq = rank_rows(quad)
    nl = len(lin) - rl; nqd = len(quad) - rq - nl
    print(f'pair {i} {j} t={t} live={len(live)} states={ns_} lin_rel={nl} quad_rel={nqd}', flush=True)
    return nqd
first = set(cand.values()); out = []
for idx, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if idx in cand: out.append((cand[idx], idx, analyse(cand[idx], idx, q.copy(), a[2])))
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP':
        u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
    elif k == 'SWAP':
        u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
    elif k == 'HMR':
        r = rng.random(N) < 0.5; bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m
    elif k == 'R': q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True
    elif k == 'BIT_STORE0': B(a[0])[m] = False
    elif k == 'BIT_STORE1': B(a[0])[m] = True
print('pairs with quadratic relations:', sum(1 for o in out if o[2] > 0), 'of', len(out))
