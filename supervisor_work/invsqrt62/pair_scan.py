"""Static scan for Toffoli pairs that can share one AND:
  CCX a b t ... CCX a c t   (same target, one shared control, nothing in between touches a,b,c,t
  except diagonal gates on a/b/c)  ->  CX c b; CCX a b t; CX c b   (saves one Toffoli)
  likewise CCZ a b t ... CCZ a c t (any qubit role, diagonal so all commute) -> CCZ with b^c.
Usage: python pair_scan.py ops.json
"""
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
DIAG = {'Z', 'CZ', 'CCZ', 'Z_POW'}
ctx = []; depth_id = 0; ids = []
cur = 0; nxt = 1
for o in ops:  # condition-context id per op
    k = K[o[0]]
    if k == 'PUSH_CONDITION': ctx.append(cur); cur = nxt; nxt += 1
    elif k == 'POP_CONDITION': cur = ctx.pop()
    ids.append(cur)
def qubits(o):
    k = K[o[0]]
    if k in ('PUSH_CONDITION', 'POP_CONDITION', 'NEG', 'BIT_INVERT', 'BIT_STORE0', 'BIT_STORE1'): return []
    if k == 'Z_POW': return [o[1]]
    if k == 'HMR': return [o[1]]
    return o[1:-1]
cnt = 0
for i, o in enumerate(ops):
    k = K[o[0]]
    if k not in ('CCX', 'CCZ'): continue
    for j in range(i + 1, min(len(ops), i + 400)):
        p = ops[j]; kp = K[p[0]]
        if kp in ('PUSH_CONDITION', 'POP_CONDITION'): break
        if kp == k and ids[j] == ids[i] and p[-1] == o[-1]:
            if k == 'CCX' and p[3] == o[3]:
                sh = set(o[1:3]) & set(p[1:3])
                if len(sh) == 1:
                    print(i, j, k, o, p); cnt += 1; break
            if k == 'CCZ':
                s1, s2 = set(o[1:4]), set(p[1:4])
                if len(s1 & s2) == 2:
                    print(i, j, k, o, p); cnt += 1; break
        qs = set(qubits(p))
        busy = set(o[1:-1])
        if not qs & busy: continue
        if kp in DIAG and (k == 'CCZ' or o[3] not in qs): continue
        break
print(cnt, 'pairs')
