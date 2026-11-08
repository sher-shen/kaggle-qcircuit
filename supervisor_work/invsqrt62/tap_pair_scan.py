"""Instruction 2 of 05:25 (tap-stream reordering), sampled necessary condition (supervisor 2026-11-08 06 UTC).
Each phase tap computes a value v_k into the tap wire with 2 ANDs, rotates it (Z_POW) and HMR-erases it.  Computing tap j
from tap i on the same wire ("rotate A, transform to B, rotate B") saves an AND only if v_i + v_j = g*h + r with g, h, r affine
in the wires available (live at t_i or t_j, recent measurement bits).  This scans all tap pairs (|i-j| <= DMAX) of the given
Z_POW wire inside [A,B) and tests, for g = any live wire or the XOR of two live wires at t_j (+ const), the exact criterion
f|{g=0} in V|{g=0} and f|{g=1} in V|{g=1}.  No hit => the reordering cannot go below 4 Toffoli per pair (for such g).
Usage: tap_pair_scan.py ops.json A B wire [nsample] [reps] [DMAX] [extra]"""
import json, sys, itertools
import numpy as np
d = json.load(open(sys.argv[1])); A0, B0, TW = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
ns = int(sys.argv[5]) if len(sys.argv) > 5 else 1500; REPS = int(sys.argv[6]) if len(sys.argv) > 6 else 4
DMAX = int(sys.argv[7]) if len(sys.argv) > 7 else 4; EXTRA = int(sys.argv[8]) if len(sys.argv) > 8 else 2
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
MAXX = 3 * (2**10 - 2)**2; rng = np.random.default_rng(17)
xs = np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64)
xs = np.repeat(xs, REPS); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; bitt = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
def in_span(vecs, f):
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
taps = []
for idx, o in enumerate(ops):
    if idx >= B0: break
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k == 'Z_POW' and a[0] == TW and idx >= A0:
        rb = [B(b) for b, tt in bitt.items() if idx - tt < 400 and B(b).any()]
        livew = [w for w in range(nq) if w != TW and q[w].any()]
        taps.append(dict(op=idx, v=q[TW].copy(), Q=q[livew].copy(), V=np.array([np.ones(N, bool)] + [q[w] for w in livew] + rb)))
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
print('taps', [t['op'] for t in taps], flush=True)
hits = []
for i in range(len(taps)):
    for j in range(i + 1, min(len(taps), i + 1 + DMAX)):
        Ti, Tj = taps[i], taps[j]; f = Ti['v'] ^ Tj['v']
        V = np.concatenate([Ti['V'], Tj['V']])
        lin = in_span(V, f)
        found = None; tested = 0; seen = set()
        if not lin:
            for e in range(1, EXTRA + 1):
                for combo in itertools.combinations(range(len(Tj['Q'])), e):
                    g = np.zeros(N, bool)
                    for c in combo: g ^= Tj['Q'][c]
                    if not g.any() or g.all(): continue
                    key = np.packbits(g).tobytes()
                    if key in seen: continue
                    seen.add(key); tested += 1
                    if in_span(V[:, ~g], f[~g]) and in_span(V[:, g], f[g]): found = combo; break
                if found is not None: break
        print(f"taps {Ti['op']} {Tj['op']} affine={lin} tested={tested} ->", 'HIT' if (lin or found is not None) else 'none', found, flush=True)
        if lin or found is not None: hits.append((Ti['op'], Tj['op']))
print('hits', len(hits), hits)
