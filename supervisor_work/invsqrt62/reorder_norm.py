# Supervisor 2026-11-12 02:xx UTC. Generic legal reorder of the normalize shifter (p62m3 layout): every CSWAP in [R0,R1) whose
# data wires are not touched by any later anchored op of [R0,R1) is moved behind R1 (same order, control form preserved
# with free CX among CTL wires), so it joins the pure CSWAP window starting at R1 (44+45 network up to T1).
# Anchors: every non-CSWAP op not purely on CTL wires (wire-22 tricks, HMR/CZ fix-ups) and CSWAPs blocked by them.
# Usage: python3 reorder_norm.py p62m3.json R0 R1 T1 CTL(comma) out.json   -> prints window [A,B)
import json, sys, itertools
from collections import deque
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
R0, R1, T1 = map(int, sys.argv[2:5]); CTL = [int(c) for c in sys.argv[5].split(',')]; n = len(CTL); ci = {c: i for i, c in enumerate(CTL)}
m = {c: 1 << i for i, c in enumerate(CTL)}; form = {}
for i in range(R0, R1):
    o = ops[i]; k = K[o[0]]
    if k == 'CX' and o[1] in ci and o[2] in ci: m[o[2]] ^= m[o[1]]
    elif k == 'CSWAP' and o[1] in ci: form[i] = m[o[1]]
S_end = tuple(m[c] for c in CTL)
def wires(o):
    k = K[o[0]]; a = o[1:-1] if k != 'Z_POW' else o[1:2]
    if k in ('HMR', 'R', 'M'): a = o[1:2]
    if k == 'CZ': return {w for w in o[1:3] if w not in ci}
    if k == 'Z': return set() if o[1] in ci else {o[1]}
    return {w for w in a if not (w in ci and k in ('CSWAP', 'CX'))} if k in ('CSWAP',) else set(a)
T = set(); moved = []
for i in range(R1 - 1, R0 - 1, -1):
    o = ops[i]; k = K[o[0]]
    if k == 'CX' and o[1] in ci and o[2] in ci: continue
    if k == 'CSWAP' and o[1] in ci and not ({o[2], o[3]} & T): moved.append(i); continue
    T |= wires(o)
    if k == 'CSWAP': T |= {o[2], o[3]}
moved = sorted(moved)
def bfs(start, goal):
    Q = deque([(start, [])]); seen = {start}
    while Q:
        s, p = Q.popleft()
        if goal(s): return s, p
        for a, b in itertools.permutations(range(n), 2):
            t = list(s); t[b] ^= t[a]; t = tuple(t)
            if t not in seen: seen.add(t); Q.append((t, p + [[KI['CX'], CTL[a], CTL[b], -1]]))
front = [ops[i] for i in range(R0, R1) if i not in set(moved)]
st = S_end; win = []
for i in moved:
    st, p = bfs(st, lambda s: form[i] in s); win += p
    win.append([KI['CSWAP'], CTL[st.index(form[i])], ops[i][2], ops[i][3], -1])
st, p = bfs(st, lambda s: s == S_end); win += p
win += ops[R1:T1]
new = ops[:R0] + front + win + ops[T1:]
sh = len(new) - len(ops); Z = d['zpow_exact']; assert all(int(k) < R0 or int(k) >= T1 for k in Z)
d['zpow_exact'] = {str(int(k) + (sh if int(k) >= T1 else 0)): v for k, v in Z.items()}
d['ops'] = new; d['n_ops'] = len(new); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[6], 'w'))
A = R0 + len(front)
print('moved', len(moved), moved, 'window', A, A + len(win))
