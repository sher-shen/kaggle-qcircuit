"""Functional (sampled) version of the merge2 building block.  For every pair of CCX gates i<j with the same target t,
where t is only XORed into (CX/CCX/X targets) between them, test on samples whether
    p_i + p_j  =  g*h + r
with g, h in span(const, the four control values; evaluated at op j) and r affine in the live wires at op j (t excluded)
plus recent classical measurement bits.  g, h and r must also lie in span(live wires at j, const) so that one CCX + CNOTs
(+ classically controlled X) can replace the two CCX.  Each x is repeated REPS times (HMR outcomes, see README).
Usage: func_pair_scan.py ops.json [nsample] [reps] [maxgap] [A] [B]"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 16; MAXGAP = int(sys.argv[4]) if len(sys.argv) > 4 else 60
A0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0; B0 = int(sys.argv[6]) if len(sys.argv) > 6 else 10**9
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(7)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; bitt = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
def basis_of(vecs):
    basis = {}
    for v in vecs:
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; break
    return basis
def red(basis, t):
    while t:
        p = t.bit_length() - 1
        if p in basis: t ^= basis[p]
        else: return t
    return 0
QA = {'CX': 2, 'CCX': 3, 'CSWAP': 3, 'SWAP': 2, 'X': 1, 'Z': 1, 'CZ': 2, 'CCZ': 3, 'HMR': 1, 'R': 1, 'Z_POW': 1, 'S': 1, 'T': 1}
# static pass: candidate pairs
cand = {}
for i, o in enumerate(ops):
    if not (A0 <= i < B0) or K[o[0]] != 'CCX': continue
    t = o[3]
    for j in range(i + 1, min(len(ops), i + MAXGAP)):
        kj = K[ops[j][0]]; aj = ops[j][1:]
        if kj in ('PUSH_CONDITION', 'POP_CONDITION', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'NEG'): continue
        qa = aj[:QA.get(kj, 0)]
        if t not in qa: continue
        if kj == 'CCX' and aj[2] == t and t not in aj[:2]: cand[j] = i; break
        if kj in ('CX',) and aj[1] == t: continue
        if kj == 'X': continue
        break
print('candidate pairs', len(cand), file=sys.stderr, flush=True)
first = {i for i in cand.values()}; pval = {}; hits = []; pend = []
for idx, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k == 'CCX' and idx in first: pval[idx] = (q[a[0]] & q[a[1]] & m, q[a[0]].copy(), q[a[1]].copy(), m.copy())
    if k == 'CCX' and idx in cand:
        i = cand[idx]; p1, c1, c2, m1 = pval.pop(i); p2 = q[a[0]] & q[a[1]] & m
        if (m1 == m).all() and m.any():
            f = toint(p1 ^ p2); t = a[2]
            live = [toint(q[w]) for w in range(nq) if w != t and q[w].any()] + [toint(np.ones(N, bool))]
            rb = [toint(B(b)) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            bl = basis_of(live); ba = basis_of(live + rb)
            ctr = [c1, c2, q[a[0]], q[a[1]], np.ones(N, bool)]
            sp = []
            for msk in range(1, 32):
                v = np.zeros(N, bool)
                for tt in range(5):
                    if (msk >> tt) & 1: v ^= ctr[tt]
                if red(bl, toint(v)) == 0: sp.append(v)
            res = [f ^ toint(g & h & m) for g, h in itertools.combinations(sp, 2)]
            pend.append((t, i, idx, res, float(m.mean())))
    if pend and k in QA:
        qa = a[:QA[k]]; keep = []
        live = None
        for (t, i, j, res, fr) in pend:
            if live is None:
                live = [toint(q[w]) for w in range(nq) if q[w].any()] + [toint(np.ones(N, bool))]
                rb = [toint(B(b)) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
                ba = basis_of(live + rb)
            liveT = basis_of([toint(q[w]) for w in range(nq) if w != t and q[w].any()] + [toint(np.ones(N, bool))] + rb)
            if any(red(liveT, r) == 0 for r in res):
                hits.append((i, j, idx)); print('HIT', i, j, 'remainder available at', idx, 'exec', fr, flush=True); continue
            t_read = (t in qa) and not ((k == 'CX' and a[1] == t and a[0] != t) or (k == 'CCX' and a[2] == t and t not in a[:2]) or k == 'X')
            if not t_read and idx - j < 400: keep.append((t, i, j, res, fr))
        pend = keep
    if k == 'X': q[a[0]] ^= m
    elif k == 'CX': q[a[1]] ^= m & q[a[0]]
    elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]
    elif k == 'CSWAP':
        u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw
    elif k == 'SWAP':
        u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
    elif k == 'HMR':
        r = rng.random(N) < 0.5; bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m; bitt[a[1]] = idx
    elif k == 'R': q[a[0]] &= ~m
    elif k == 'BIT_INVERT': B(a[0])[m] ^= True; bitt[a[0]] = idx
    elif k == 'BIT_STORE0': B(a[0])[m] = False; bitt[a[0]] = idx
    elif k == 'BIT_STORE1': B(a[0])[m] = True; bitt[a[0]] = idx
print('hits', len(hits), hits)
