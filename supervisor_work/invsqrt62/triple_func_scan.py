"""TRIPLE (3 -> 2) version, derived from func_affine_scan.py (supervisor 2026-11-08 06 UTC).
For same-target CCX triples i<j<k (consecutive same-target pairs i->j, j->k), f = p_i + p_j + p_k sampled at op k.
Necessary condition for f = g1*h1 + g2*h2 + r (r, h affine in V): f restricted to each quadrant {g1=b, g2=c} lies in V.
g1, g2 range over XORs of <= 2 of the six control values (+const). Hits are relaxations and need a manual check.
--- original doc of func_affine_scan: General affine-factor version of func_pair_scan (supervisor 2026-11-08 06 UTC, instruction 1 of 05:25).
For each pair of CCX i<j into the same target t (t only XORed into between them), f = p_i + p_j sampled at op j.
Exact criterion: f = g*h + r with g, h, r affine in V = span(1, live wires at j except t, recent measurement bits)
  <=>  f restricted to {g=0} is in V|{g=0}  and  f restricted to {g=1} is in V|{g=1}   (then h = r0 + r1).
g is searched over span(1, 4 control values) + up to EXTRA further live wires (weight-limited, not all of 2^61).
Also tests the 3->2 version for same-target triples (f = sum of 3 products = g1 h1 + g2 h2 + r) is NOT done here.
Usage: func_affine_scan.py ops.json [nsample] [reps] [maxgap] [extra]"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 4; MAXGAP = int(sys.argv[4]) if len(sys.argv) > 4 else 60
EXTRA = int(sys.argv[5]) if len(sys.argv) > 5 else 1
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(13)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; bitt = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
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
def in_span(vecs, f):
    """vecs: (n, M) bool, f: (M,) bool -> is f in GF(2) row span"""
    if vecs.shape[1] == 0: return True
    toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
    basis = {}
    for v in vecs:
        v = toint(v)
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; break
    t = toint(f)
    while t:
        p = t.bit_length() - 1
        if p in basis: t ^= basis[p]
        else: return False
    return True
trip = {k_: (cand[j_], j_) for k_, j_ in cand.items() if j_ in cand}
print('triples', len(trip), file=sys.stderr, flush=True)
need = set(); [need.update(v) for v in trip.values()]
pval = {}; hits = []; pend = []
for idx, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k == 'CCX' and idx in need: pval[idx] = (q[a[0]] & q[a[1]] & m, q[a[0]].copy(), q[a[1]].copy(), m.copy())
    if k == 'CCX' and idx in trip:
        i, j = trip[idx]; P1, P2 = pval[i], pval[j]; p3 = q[a[0]] & q[a[1]] & m; t = a[2]
        if (P1[3] == m).all() and (P2[3] == m).all() and m.any():
            f = P1[0] ^ P2[0] ^ p3
            livew = [w for w in range(nq) if w != t and q[w].any()]
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            V0 = np.array([np.ones(N, bool)] + [q[w] for w in livew] + rb)
            ctr = [P1[1], P1[2], P2[1], P2[2], q[a[0]], q[a[1]]]
            gs = []
            for e in (1, 2):
                for cmb in itertools.combinations(range(6), e):
                    v = np.zeros(N, bool)
                    for c in cmb: v ^= ctr[c]
                    if v.any() and not v.all(): gs.append(v)
            pend.append(dict(i=i, j=j, k=idx, t=t, f=f, V=V0, gs=gs, fr=float(m.mean())))
    if pend and k in QA:
        qa = a[:QA[k]]; keep = []
        for P in pend:
            t = P['t']
            t_read = (t in qa) and not ((k == 'CX' and a[1] == t and a[0] != t) or (k == 'CCX' and a[2] == t and t not in a[:2]) or k == 'X')
            if not t_read and idx - P['k'] < 400 and idx != len(ops) - 1: keep.append(P); continue
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            V = np.concatenate([P['V'], np.array([q[w] for w in range(nq) if w != t and q[w].any()] + rb)]); f = P['f']
            found = None; gs = P['gs']
            for x1 in range(len(gs)):
                for x2 in range(x1 + 1, len(gs)):
                    g1, g2 = gs[x1], gs[x2]; ok = True
                    for b in (False, True):
                        for c in (False, True):
                            sel = (g1 == b) & (g2 == c)
                            if sel.any() and not in_span(V[:, sel], f[sel]): ok = False; break
                        if not ok: break
                    if ok: found = (x1, x2); break
                if found: break
            print(f"triple {P['i']} {P['j']} {P['k']} t={t} exec={P['fr']:.3f} end={idx} ->", 'HIT' if found else 'none', found, flush=True)
            if found: hits.append((P['i'], P['j'], P['k']))
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
