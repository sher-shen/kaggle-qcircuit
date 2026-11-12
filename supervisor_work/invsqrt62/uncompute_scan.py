"""Find unconditioned CCX that uncompute: after the CCX the target's formal value (from stage_xag.py json, formal variables = wires
at stage start + ANDs) contains no AND term (it is affine in the stage-start wires), i.e. the Toffoli only removed a product.
Such a Toffoli could in principle be replaced by HMR + classically controlled CZ (0 Toffoli) if the affine remainder is cleared by CNOTs.
Usage: uncompute_scan.py ops.json A B"""
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
A, B = int(sys.argv[2]), int(sys.argv[3])
W = [(1 << w) for w in range(nq)]; nf = [0]; nand = [0]
def fresh(): nf[0] += 1; return 1 << (nq + 10**6 + nf[0])
cond = sum({'PUSH_CONDITION': 1, 'POP_CONDITION': -1}.get(K[o[0]], 0) for o in ops[:A])
amask = 0; hits = []; prod = {}
for i in range(A, B):
    o = ops[i]; k = K[o[0]]; a = o[1:]
    if k == 'PUSH_CONDITION': cond += 1; continue
    if k == 'POP_CONDITION': cond -= 1; continue
    if k in ('NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1', 'Z', 'CZ', 'CCZ', 'Z_POW', 'X'): continue
    if k == 'CX': W[a[1]] = W[a[1]] ^ W[a[0]] if not cond else fresh()
    elif k == 'SWAP':
        if cond: W[a[0]] = fresh(); W[a[1]] = fresh()
        else: W[a[0]], W[a[1]] = W[a[1]], W[a[0]]
    elif k in ('HMR', 'R'): W[a[0]] = 0
    elif k == 'CSWAP': W[a[1]] = fresh(); W[a[2]] = fresh()
    elif k == 'CCX':
        if cond: W[a[2]] = fresh(); continue
        key = frozenset([W[a[0]], W[a[1]]])
        if key in prod: v = prod[key]
        else: v = 1 << (nq + nand[0]); nand[0] += 1; prod[key] = v
        W[a[2]] ^= v
        if (W[a[2]] >> nq) == 0: hits.append(i)
print('CCX', nand[0], 'uncompute-type CCX', len(hits), hits[:40])
