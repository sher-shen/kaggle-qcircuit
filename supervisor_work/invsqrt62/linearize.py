"""Replace Toffoli-class gates whose product is affine-linear in the other live wires (found on a sample of x)
by the equivalent Clifford gates: CCZ -> Z on each wire of the parity (+NEG for the constant), same condition;
CCX -> CX from each wire of the parity into the target (+X for the constant), same condition.
Only gates executed on >= minfrac of the sampled shots are replaced. The result MUST be checked with the
official verifier on all x (it is exact; the sample is only a search heuristic).
Usage: python linearize.py ops.json out_ops.json [minfrac] [nsample] [skip_ops_comma] [shots_per_x]
Each sampled x is repeated shots_per_x times so that measurement-outcome-dependent wire values are covered.
"""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1])); dst = sys.argv[2]
minfrac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
ns = int(sys.argv[4]) if len(sys.argv) > 4 else 8000
skip = set(int(t) for t in sys.argv[5].split(',')) if len(sys.argv) > 5 and sys.argv[5] else set()
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']; KI = {k: i for i, k in enumerate(K)}
MAXX = 3 * (2**10 - 2)**2
rng = np.random.default_rng(11)
reps = int(sys.argv[6]) if len(sys.argv) > 6 else 32
xs = np.repeat(np.unique(np.concatenate([np.arange(1, 1025), rng.integers(1, MAXX + 1, ns)])).astype(np.int64), reps); N = len(xs)
q = np.zeros((nq, N), bool)
for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
bits = {}; B = lambda i: bits.setdefault(i, np.zeros(N, bool)); stack = []; act = np.ones(N, bool)
toint = lambda v: int.from_bytes(np.packbits(v).tobytes(), 'big')
def solve(vecs, t):  # vecs: list of (label, int); returns set of labels whose XOR == t, or None
    basis = {}
    for lab, v in vecs:
        comb = {lab}
        while v:
            p = v.bit_length() - 1
            if p in basis: v ^= basis[p][0]; comb ^= basis[p][1]
            else: basis[p] = (v, comb); break
    comb = set()
    while t:
        p = t.bit_length() - 1
        if p not in basis: return None
        t ^= basis[p][0]; comb ^= basis[p][1]
    return comb
repl = {}
for i, o in enumerate(ops):
    k = K[o[0]]
    if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
    if k == 'POP_CONDITION': act = stack.pop(); continue
    cond = o[-2] if k == 'Z_POW' else o[-1]
    m = act & B(cond) if cond >= 0 else act; a = o[1:]
    if k in ('CCX', 'CCZ') and m.mean() >= minfrac and i not in skip:
        if k == 'CCX': prod = q[a[0]] & q[a[1]]; excl = {a[2]}
        else: prod = q[a[0]] & q[a[1]] & q[a[2]]; excl = set()
        vecs = [(j, toint(q[j] & m)) for j in range(nq) if j not in excl and (q[j] & m).any()] + [('1', toint(m))]
        comb = solve(vecs, toint(prod & m))
        if comb is not None:
            c = cond
            if k == 'CCZ': new = [[KI['Z'], j, c] for j in sorted(w for w in comb if w != '1')] + ([[KI['NEG'], c]] if '1' in comb else [])
            else: new = [[KI['CX'], j, a[2], c] for j in sorted(w for w in comb if w != '1')] + ([[KI['X'], a[2], c]] if '1' in comb else [])
            repl[i] = new; print('replace', i, k, a[:3], 'frac %.4f' % m.mean(), '->', sorted(map(str, comb)), flush=True)
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
newops = []; zp = {}
for i, o in enumerate(ops):
    if i in repl: newops += repl[i]; continue
    if str(i) in d['zpow_exact']: zp[str(len(newops))] = d['zpow_exact'][str(i)]
    newops.append(o)
d2 = dict(d); d2['ops'] = newops; d2['n_ops'] = len(newops); d2['zpow_exact'] = zp; d2['source_kmb_sha256'] = None
json.dump(d2, open(dst, 'w'))
print('replaced', len(repl), 'gates')
