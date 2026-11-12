"""Symbolic AND-level affine form of any op range [A,B) of ops.json. Formal variables = the nq wire values at op A
(bit w), AND i = bit nq+i. HMR/R reset the wire to 0 (the measured value counts as a consumer); CZ/Z/CCZ operands count
as consumers; PUSH/POP_CONDITION are ignored (ops inside them are only phase ops / HMR here, checked).
Writes json {nv0, ands:[[maskA,cA,maskB,cB]], cons:[[and_index_or_-1, mask]]}.  Usage: stage_xag.py ops.json A B out.json"""
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; nq = d['n_qubits']
A, B = int(sys.argv[2]), int(sys.argv[3])
W = [(1 << w, 0) for w in range(nq)]
ands = []; cons = []; cond = sum({'PUSH_CONDITION': 1, 'POP_CONDITION': -1}.get(K[o[0]], 0) for o in ops[:A]); nfresh = 0; opidx = []
for i in range(A, B):
    o = ops[i]; k = K[o[0]]; a = o[1:]
    if k == 'PUSH_CONDITION': cond += 1; continue
    if k == 'POP_CONDITION': cond -= 1; continue
    if cond and k in ('SWAP', 'CSWAP'):  # conditional swap: both wires consumed and replaced by fresh variables
        for q in (a[:2] if k == "SWAP" else a[:3]):
            cons.append((-1, W[q][0]))
        for q in (a[:2] if k == 'SWAP' else a[1:3]):
            W[q] = (1 << (nq + 100000 + nfresh), 0); nfresh += 1
        continue
    if cond and k == 'CCX':  # classically controlled Toffoli: controls consumed, target XOR fresh variable (not a window AND)
        cons.append((-1, W[a[0]][0])); cons.append((-1, W[a[1]][0]))
        W[a[2]] = (W[a[2]][0] ^ (1 << (nq + 100000 + nfresh)), W[a[2]][1]); nfresh += 1; continue
    if k == 'CSWAP':  # = CX(t2->t1) CCX(c,t1->t2) CX(t2->t1)
        c_, t1, t2 = a[0], a[1], a[2]
        W[t1] = (W[t1][0] ^ W[t2][0], W[t1][1] ^ W[t2][1])
        j = len(ands); ands.append((W[c_], W[t1])); opidx.append(i)
        cons.append((j, W[c_][0])); cons.append((j, W[t1][0]))
        W[t2] = (W[t2][0] ^ (1 << (nq + j)), W[t2][1])
        W[t1] = (W[t1][0] ^ W[t2][0], W[t1][1] ^ W[t2][1]); continue
    if cond and k == 'CX':  # classically controlled CX: control consumed, target XOR fresh variable
        cons.append((-1, W[a[0]][0])); W[a[1]] = (W[a[1]][0] ^ (1 << (nq + 100000 + nfresh)), W[a[1]][1]); nfresh += 1; continue
    if cond and k == 'X':  # classically controlled flip: XOR a fresh formal variable
        W[a[0]] = (W[a[0]][0] ^ (1 << (nq + 100000 + nfresh)), W[a[0]][1]); nfresh += 1; continue
    if k in ('NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1'): continue
    if k == 'Z_POW': cons.append((-1, W[a[0]][0])); continue
    if k == 'X': W[a[0]] = (W[a[0]][0], W[a[0]][1] ^ 1)
    elif k == 'CX': W[a[1]] = (W[a[1]][0] ^ W[a[0]][0], W[a[1]][1] ^ W[a[0]][1])
    elif k == 'SWAP': W[a[0]], W[a[1]] = W[a[1]], W[a[0]]
    elif k == 'CCX':
        j = len(ands); ands.append((W[a[0]], W[a[1]])); opidx.append(i)
        cons.append((j, W[a[0]][0])); cons.append((j, W[a[1]][0]))
        W[a[2]] = (W[a[2]][0] ^ (1 << (nq + j)), W[a[2]][1])
    elif k in ('HMR', 'R'):
        cons.append((-1, W[a[0]][0])); W[a[0]] = (0, 0)
    elif k in ('CZ', 'Z', 'CCZ', 'S', 'T'):
        for q in a[:{'CZ': 2, 'Z': 1, 'CCZ': 3, 'S': 1, 'T': 1}[k]]: cons.append((-1, W[q][0]))
    else: raise SystemExit(f'unhandled {k} at {i}')
for w in range(nq): cons.append((-1, W[w][0]))
json.dump({'nv0': nq, 'ands': [[hex(x[0]), x[1], hex(y[0]), y[1]] for x, y in ands],
           'cons': [[j, hex(m)] for j, m in cons], 'opidx': opidx}, open(sys.argv[4], 'w'))
print('ands', len(ands), 'cons', len(cons))
