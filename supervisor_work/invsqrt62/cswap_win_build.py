# Supervisor 2026-11-12 02:xx UTC. Generic builder for cswap_win_sa.c solutions: replace the pure CSWAP window [A,B) of
# ops.json (as extracted by cswap_win_extract.py) by the SA network. Each gate's control form (mask over CTL bits at A) is
# put on some control wire with free CX among the CTL wires (BFS), and the CTL wires are restored to their original end forms.
# Usage: python3 cswap_win_build.py ops.json win.json sa.log out.json
import json, sys, re, itertools
from collections import deque
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
w = json.load(open(sys.argv[2])); A, B, CTL, data = w['A'], w['B'], w['CTL'], w['data']
gates = [tuple(map(int, m.groups())) for l in open(sys.argv[3]) for m in [re.match(r'gate \d+ pair (\d+) (\d+) form (\d+)', l)] if m]
n = len(CTL); m = {c: 1 << i for i, c in enumerate(CTL)}
for i in range(A, B):
    o = ops[i]
    if K[o[0]] == 'CX': m[o[2]] ^= m[o[1]]
endst = tuple(m[c] for c in CTL)
def bfs(start, goal):
    Q = deque([(start, [])]); seen = {start}
    while Q:
        s, p = Q.popleft()
        if goal(s): return s, p
        for i, j in itertools.permutations(range(n), 2):
            t = list(s); t[j] ^= t[i]; t = tuple(t)
            if t not in seen: seen.add(t); Q.append((t, p + [[KI['CX'], CTL[i], CTL[j], -1]]))
st = tuple(1 << i for i in range(n)); new = []
for a, b, f in gates:
    st, p = bfs(st, lambda s: f in s); new += p
    new.append([KI['CSWAP'], CTL[st.index(f)], data[a], data[b], -1])
st, p = bfs(st, lambda s: s == endst); new += p
Z = d['zpow_exact']; assert all(int(k) < A or int(k) >= B for k in Z)
sh = len(new) - (B - A)
d['zpow_exact'] = {str(int(k) + (sh if int(k) >= B else 0)): v for k, v in Z.items()}
d['ops'] = ops[:A] + new + ops[B:]; d['n_ops'] = len(d['ops']); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[4], 'w'))
print('gates', len(gates), 'region ops', len(new), 'CSWAP', sum(K[o[0]] == 'CSWAP' for o in new))
