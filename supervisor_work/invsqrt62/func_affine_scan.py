"""General affine-factor version of func_pair_scan (supervisor 2026-11-08 06 UTC, instruction 1 of 05:25).
For each pair of CCX i<j into the same target t (t only XORed into between them), f = p_i + p_j sampled at op j.
Exact criterion: f = g*h + r with g, h, r affine in V = span(1, live wires at j except t, recent measurement bits)
  <=>  f restricted to {g=0} is in V|{g=0}  and  f restricted to {g=1} is in V|{g=1}   (then h = r0 + r1).
g is searched over span(1, 4 control values) + up to EXTRA further live wires (weight-limited, not all of 2^61).
Also tests the 3->2 version for same-target triples (f = sum of 3 products = g1 h1 + g2 h2 + r) is NOT done here.
Usage: func_affine_scan.py ops.json [nsample] [reps] [maxgap] [extra] [A] [B]  (first CCX of the pair in [A,B))"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 4; MAXGAP = int(sys.argv[4]) if len(sys.argv) > 4 else 60
EXTRA = int(sys.argv[5]) if len(sys.argv) > 5 else 1
A0 = int(sys.argv[6]) if len(sys.argv) > 6 else 0; B0 = int(sys.argv[7]) if len(sys.argv) > 7 else 10**9
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
    if K[o[0]] != 'CCX' or not (A0 <= i < B0): continue
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
first = set(cand.values()); pval = {}; hits = []; nt = 0; pend = []
for idx, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k == 'CCX' and idx in first: pval[idx] = (q[a[0]] & q[a[1]] & m, q[a[0]].copy(), q[a[1]].copy(), m.copy())
    if k == 'CCX' and idx in cand:
        i = cand[idx]; p1, c1, c2, m1 = pval.pop(i); p2 = q[a[0]] & q[a[1]] & m; t = a[2]
        if (m1 == m).all() and m.any():
            f = p1 ^ p2
            livew = [w for w in range(nq) if w != t and q[w].any()]
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            V = np.array([np.ones(N, bool)] + [q[w] for w in livew] + rb)
            ctr = [c1, c2, q[a[0]], q[a[1]]]
            base = []
            for msk in range(1, 16):
                v = np.zeros(N, bool)
                for tt in range(4):
                    if (msk >> tt) & 1: v ^= ctr[tt]
                base.append(v)
            # g must itself be in V (computable): keep only those
            base = [v for v in base if in_span(V, v)]
            ext = [np.zeros(N, bool)] + [q[w] for w in livew]
            pend.append(dict(i=i, j=idx, t=t, f=f, V=V, base=base, livew=livew, Q=q[livew].copy(), fr=float(m.mean())))
    if pend and k in QA:
        qa = a[:QA[k]]; keep = []
        for P in pend:
            t = P['t']
            t_read = (t in qa) and not ((k == 'CX' and a[1] == t and a[0] != t) or (k == 'CCX' and a[2] == t and t not in a[:2]) or k == 'X')
            if not t_read and idx - P['j'] < 400 and idx != len(ops) - 1: keep.append(P); continue
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            Vend = np.array([q[w] for w in range(nq) if w != t and q[w].any()] + rb)
            V = np.concatenate([P['V'], Vend]); f = P['f']; livew = P['livew']; Qj = P['Q']
            found = None; tested = 0; seen = set()
            for bv in [np.zeros(N, bool)] + P['base']:
                for e in range(0, EXTRA + 1):
                    for combo in itertools.combinations(range(len(livew)), e):
                        g = bv.copy()
                        for c in combo: g ^= Qj[c]
                        if not g.any() or g.all(): continue
                        key = np.packbits(g).tobytes()
                        if key in seen: continue
                        seen.add(key); tested += 1
                        z = ~g
                        if in_span(V[:, z], f[z]) and in_span(V[:, g], f[g]):
                            found = combo; break
                    if found is not None: break
                if found is not None: break
            nt += tested
            print(f"pair {P['i']} {P['j']} t={t} exec={P['fr']:.3f} end={idx} tested={tested} ->", 'HIT' if found is not None else 'none', found, flush=True)
            if found is not None: hits.append((P['i'], P['j']))
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
print('hits', len(hits), hits, 'g tested', nt)
