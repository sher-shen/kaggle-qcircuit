"""Commutation-aware scan for Toffoli pairs that can share one AND (generalises pair_scan.py).
Each op gets a role per qubit: 'Z' (control / diagonal), 'X' (X-type target), 'O' (anything else:
SWAP, CSWAP targets, R, HMR). Two ops commute if every shared qubit has role Z in both or X in both.
Pairs (same condition context and same condition bit, bit not rewritten in between):
  CCX a b t ... CCX a c t   ->  CX c b; CCX a b t; CX c b        (-1 Toffoli)
  CCZ a b c ... CCZ a b d   ->  CX d c; CCZ a b c; CX d c        (-1 Toffoli)
  CCX a b t ... CCX a b t   ->  delete both                      (-2)
Gate j may be moved back to i, or gate i forward to j, if everything between commutes with it.
Usage: python comm_pair_scan.py ops.json [window]
"""
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
W = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
ctx = []; cur = 0; nxt = 1; ids = []
for o in ops:
    k = K[o[0]]
    if k == 'PUSH_CONDITION': ctx.append(cur); cur = nxt; nxt += 1; ids.append(ctx[-1])
    elif k == 'POP_CONDITION': ids.append(cur); cur = ctx.pop()
    else: ids.append(cur)
def roles(o):
    k = K[o[0]]; a = o[1:]
    if k == 'X': return {a[0]: 'X'}
    if k == 'CX': return {a[0]: 'Z', a[1]: 'X'}
    if k == 'CCX': return {a[0]: 'Z', a[1]: 'Z', a[2]: 'X'}
    if k in ('Z',): return {a[0]: 'Z'}
    if k == 'CZ': return {a[0]: 'Z', a[1]: 'Z'}
    if k == 'CCZ': return {a[0]: 'Z', a[1]: 'Z', a[2]: 'Z'}
    if k == 'Z_POW': return {a[0]: 'Z'}
    if k == 'SWAP': return {a[0]: 'O', a[1]: 'O'}
    if k == 'CSWAP': return {a[0]: 'Z', a[1]: 'O', a[2]: 'O'}
    if k in ('R', 'HMR'): return {a[0]: 'O'}
    return {}
def wbits(o):
    k = K[o[0]]
    if k == 'HMR': return {o[2]}
    if k in ('BIT_STORE0', 'BIT_STORE1'): return {o[1]}
    if k == 'BIT_INVERT': return {o[1]}
    return set()
R = [roles(o) for o in ops]
def comm(r1, r2):
    for q, v in r1.items():
        w = r2.get(q)
        if w is not None and (v != w or v == 'O'): return False
    return True
def cond(o): return o[-1]
hits = []
for i, o in enumerate(ops):
    k = K[o[0]]
    if k not in ('CCX', 'CCZ'): continue
    okj_block = False  # j-move-back blocked?
    for j in range(i + 1, min(len(ops), i + W)):
        p = ops[j]; kp = K[p[0]]
        if kp == k and ids[j] == ids[i] and cond(p) == cond(o):
            typ = None
            if k == 'CCX' and p[3] == o[3]:
                sh = set(o[1:3]) & set(p[1:3])
                if len(sh) == 2: typ = 'same'
                elif len(sh) == 1: typ = 'share1'
            if k == 'CCZ' and len(set(o[1:4]) & set(p[1:4])) >= 2:
                typ = 'same' if set(o[1:4]) == set(p[1:4]) else 'share2'
            if typ:
                # can j move back to i (all between commute with p)?  or i forward?
                bc = cond(o)
                ok_bits = all(bc == -1 or bc not in wbits(ops[m]) for m in range(i + 1, j))
                back = ok_bits and all(comm(R[j], R[m]) for m in range(i + 1, j))
                fwd = ok_bits and all(comm(R[i], R[m]) for m in range(i + 1, j))
                if back or fwd:
                    hits.append((i, j, typ, o, p, back, fwd)); print(i, j, typ, o, p, 'back' if back else 'fwd', flush=True)
        # stop when gate i can no longer move forward AND nothing behind can come back meaningfully: keep simple bound
        if False:
            break
print(len(hits), 'pairs')
