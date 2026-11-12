"""Window-resynthesis lower bound for the coeff_lookup XAG (xag_affine.py output).
Premise (checked here): truth tables of const, 8 inputs and all 177 ANDs are GF(2)-independent.
Then replacing a set W of k ANDs by k-1 new ANDs (all other ANDs keep their functions) is possible
only if the W-projections of all consumer masks (operands of ANDs outside W + outputs) have rank <= k-1.
Scans: all consecutive windows k=2..K, all pairs, all triples among ANDs with a common consumer.
Usage: xag_window_rank.py xag.json [K]"""
import json, sys, itertools
d = json.load(open(sys.argv[1])); K = int(sys.argv[2]) if len(sys.argv) > 2 else 8
A = [(int(a, 16), ca, int(b, 16), cb) for a, ca, b, cb in d['ands']]
O = [(int(m, 16), c) for m, c in d['outs']]
N = len(A)
FULL = (1 << 256) - 1
tt = [sum(1 << x for x in range(256) if (x >> i) & 1) for i in range(8)]
def ev(m, c):
    r = FULL if c else 0; k = 0
    while m:
        if m & 1: r ^= tt[k]
        m >>= 1; k += 1
    return r
for a, ca, b, cb in A: tt.append(ev(a, ca) & ev(b, cb))
# independence check of [const] + tt
def rank(vecs):
    basis = {}
    r = 0
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis: v ^= basis[h]
            else: basis[h] = v; r += 1; break
    return r
print('independence: rank', rank([FULL] + tt), 'of', 1 + len(tt))
# consumers: list of (consumer_id, mask); consumer id = AND index or 'o'
cons = []
for j, (a, ca, b, cb) in enumerate(A): cons += [(j, a), (j, b)]
for m, c in O: cons.append((-1, m))
def wrank(W):
    Ws = set(W); bits = [8 + w for w in W]
    vecs = []
    for j, m in cons:
        if j in Ws: continue
        v = 0
        for t, bb in enumerate(bits):
            if (m >> bb) & 1: v |= 1 << t
        if v: vecs.append(v)
    return rank(vecs)
hits = []
for k in range(2, K + 1):
    bad = [s for s in range(N - k + 1) if wrank(range(s, s + k)) < k]
    print(f'consecutive k={k}: {N-k+1} windows, deficient {len(bad)}', bad[:10])
    hits += bad
bad2 = [p for p in itertools.combinations(range(N), 2) if wrank(p) < 2]
print('pairs deficient', len(bad2), bad2[:10])
# per-AND: rank 1 always unless never used
unused = [i for i in range(N) if wrank([i]) == 0]
print('unused ANDs', unused)
# triples: sample all triples among 60 last ANDs (fanout smallest)
cnt = 0; bad3 = []
for t in itertools.combinations(range(N - 60, N), 3):
    cnt += 1
    if wrank(t) < 3: bad3.append(t)
print('triples (last 60 ANDs)', cnt, 'deficient', len(bad3), bad3[:10])
