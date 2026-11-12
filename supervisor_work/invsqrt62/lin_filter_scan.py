"""LINEAR RELAXATION filter (supervisor 2026-11-08 21 UTC): for each pair, test f in span(V, G_k*V) for ALL k at once;
rejection proves no g in G (any dimension) gives f = g*h + r.  Derived from support_g_scan:
Support-directed version of func_affine_scan (supervisor 2026-11-08 07 UTC, instruction 1 of 06:50).
For each same-target CCX pair i<j (as in func_affine_scan), f = p_i + p_j.  Formal window [i-L, j]: variables = wire
values at op i-L and AND outputs inside the window (CCX product / CSWAP product); measurement-conditioned ops give fresh
variables, which are dropped.  supp = variables in the formal masks of the 4 control values.
G = V  intersect  span(1, sample vectors of supp)  (exact linear algebra on the samples), and EVERY g in G (up to 2^MAXD,
else a random subset) is tested with the exact criterion  f|{g=0} in V|{g=0}  and  f|{g=1} in V|{g=1}
(V = live wires at j and at the next read of t + recent measurement bits, as in func_affine_scan).
Usage: support_g_scan.py ops.json [nsample] [reps] [maxgap] [L] [MAXD] [A] [B]"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); ns = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 4; MAXGAP = int(sys.argv[4]) if len(sys.argv) > 4 else 60
L = int(sys.argv[5]) if len(sys.argv) > 5 else 400; MAXD = int(sys.argv[6]) if len(sys.argv) > 6 else 13
A0 = int(sys.argv[7]) if len(sys.argv) > 7 else 0; B0 = int(sys.argv[8]) if len(sys.argv) > 8 else 10**9
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']; FRESH = 1 << 200000
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

def formal(A, i, j):
    """formal masks of the controls of CCX i and CCX j, window starting at op A. returns list of specs."""
    W = [1 << w for w in range(nq)]; andop = []; nf = 0
    cond = sum({'PUSH_CONDITION': 1, 'POP_CONDITION': -1}.get(K[o[0]], 0) for o in ops[:A])
    got = []
    for idx in range(A, j + 1):
        o = ops[idx]; k = K[o[0]]; a = o[1:]
        if k == 'PUSH_CONDITION': cond += 1; continue
        if k == 'POP_CONDITION': cond -= 1; continue
        if k in ('NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'Z_POW', 'Z', 'CZ', 'CCZ', 'S', 'T'): continue
        c_ = a[-1] if k not in ('HMR',) else -1
        classical = cond > 0 or (k in ('CX', 'CCX', 'CSWAP', 'SWAP', 'X') and c_ >= 0)
        if idx in (i, j): got += [W[a[0]], W[a[1]]]
        if classical:
            tg = {'X': a[:1], 'CX': a[1:2], 'CCX': a[2:3], 'SWAP': a[:2], 'CSWAP': a[1:3], 'HMR': a[:1], 'R': a[:1]}.get(k, ())
            for qq in tg: W[qq] = W[qq] ^ (FRESH << nf); nf += 1
            continue
        if k == 'X': continue
        elif k == 'CX': W[a[1]] ^= W[a[0]]
        elif k == 'SWAP': W[a[0]], W[a[1]] = W[a[1]], W[a[0]]
        elif k == 'CCX':
            W[a[2]] ^= 1 << (nq + len(andop)); andop.append(idx)
        elif k == 'CSWAP':
            c, t1, t2 = a[0], a[1], a[2]
            W[t1] ^= W[t2]; W[t2] ^= 1 << (nq + len(andop)); andop.append(idx); W[t1] ^= W[t2]
        elif k in ('HMR', 'R'): W[a[0]] = 0
    m = 0
    for x in got: m |= x
    m &= FRESH - 1
    specs = []
    for b in range(m.bit_length()):
        if (m >> b) & 1: specs.append(('w', b) if b < nq else ('a', andop[b - nq]))
    return specs

MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(17)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
pinfo = {}
snapat = {}; andneed = set()
for j, i in cand.items():
    A = max(0, i - L); sp = formal(A, i, j); pinfo[j] = (i, A, sp)
    snapat.setdefault(A, set()).update(w for t, w in sp if t == 'w')
    andneed.update(w for t, w in sp if t == 'a')
print('formal supports:', sorted(len(v[2]) for v in pinfo.values()), file=sys.stderr, flush=True)

def echelon(rows):
    basis = {}
    for v in rows:
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p]
            else: basis[p] = v; break
    return basis
def reduce(basis, t):
    while t:
        p = t.bit_length() - 1
        if p in basis: t ^= basis[p]
        else: return t
    return 0
def in_span(vecs, f):
    return reduce(echelon(toint(v) for v in vecs), toint(f)) == 0


def lin_member(rows, f):
    """exact GF(2): is f in the row span of rows (bool R x N)?  packed RREF over columns."""
    M = np.packbits(np.concatenate([rows, f[None, :]]).astype(np.uint8), axis=1)
    M = np.ascontiguousarray(M); R = M.shape[0] - 1; Mf = M[R].copy(); M = M[:R]
    rank = 0; ncol = rows.shape[1]
    for c in range(ncol):
        if rank == R: break
        byte, bit = c >> 3, 7 - (c & 7)
        colv = (M[rank:, byte] >> bit) & 1
        nz = np.flatnonzero(colv)
        if len(nz) == 0: continue
        p = rank + nz[0]
        if p != rank: M[[rank, p]] = M[[p, rank]]
        hit = ((M[:, byte] >> bit) & 1).astype(bool); hit[rank] = False
        M[hit] ^= M[rank]
        if (Mf[byte] >> bit) & 1: Mf ^= M[rank]
        rank += 1
    return not Mf.any(), rank

q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; bitt = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
snaps = {}; andval = {}; first = set(cand.values()); pval = {}; hits = []; pend = []; nt = 0
for idx, o in enumerate(ops):
    k = K[o[0]]
    if idx in snapat:
        for w in snapat[idx]: snaps[(idx, w)] = q[w].copy()
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if idx in andneed:
        andval[idx] = (q[a[0]] & q[a[1]] & m) if k == 'CCX' else (q[a[0]] & (q[a[1]] ^ q[a[2]]) & m)
    if k == 'CCX' and idx in first: pval[idx] = (q[a[0]] & q[a[1]] & m, m.copy(), q[a[0]].copy(), q[a[1]].copy())
    if k == 'CCX' and idx in cand:
        i, A, sp = pinfo[idx]; p1, m1, c1, c2 = pval.pop(i); p2 = q[a[0]] & q[a[1]] & m; t = a[2]
        if (m1 == m).all() and m.any():
            f = p1 ^ p2
            livew = [w for w in range(nq) if w != t and q[w].any()]
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            V = np.array([np.ones(N, bool)] + [q[w] for w in livew] + rb)
            S = [c1, c2, q[a[0]].copy(), q[a[1]].copy()] + [snaps[(A, w)] if tp == 'w' else andval[w] for tp, w in sp]
            # G = V cap span(S): reduce each S vector against V, find S-combos with zero residual
            vb = echelon(toint(v) for v in V); res = {}; Gb = []
            for si, s in enumerate(S):
                r = reduce(vb, toint(s)); comb = 1 << si
                while r:
                    p = r.bit_length() - 1
                    if p in res: r ^= res[p][0]; comb ^= res[p][1]
                    else: res[p] = (r, comb); break
                if not r: Gb.append(comb)
            Gv = []; gb = {}
            for comb in Gb:
                g = np.zeros(N, bool)
                for si in range(len(S)):
                    if (comb >> si) & 1: g ^= S[si]
                r = reduce(gb, toint(g))  # keep a basis of distinct sample vectors only
                if r: gb[r.bit_length() - 1] = r; Gv.append(g)
            pend.append(dict(i=i, j=idx, t=t, f=f, V=V, G=Gv, ns=len(S), fr=float(m.mean())))
    if pend and k in QA:
        qa = a[:QA[k]]; keep = []
        for P in pend:
            t = P['t']
            t_read = (t in qa) and not ((k == 'CX' and a[1] == t and a[0] != t) or (k == 'CCX' and a[2] == t and t not in a[:2]) or k == 'X')
            if not t_read and idx - P['j'] < 400 and idx != len(ops) - 1: keep.append(P); continue
            rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
            Vend = [q[w] for w in range(nq) if w != t and q[w].any()] + rb
            Vall = np.concatenate([P['V'], np.array(Vend)]); f = P['f']; G = P['G']; dg = len(G)
            rows = np.concatenate([Vall] + [Vall & g[None, :] for g in G]) if dg else Vall
            ok, rk = lin_member(rows, f); tested = 1
            found = None if not ok else 'f in V+G*V (not rejected)'
            print(f"   rows {len(rows)} rank {rk} N {N}", flush=True)
            nt += tested
            print(f"pair {P['i']} {P['j']} t={t} exec={P['fr']:.3f} |supp|={P['ns']} dimG={dg} tested={tested} ->",
                  'HIT' if found is not None else 'none', found, flush=True)
            if found is not None: hits.append((P['i'], P['j'], dg))
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
