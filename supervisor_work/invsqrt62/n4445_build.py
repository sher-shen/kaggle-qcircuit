# Supervisor 2026-11-12 01:xx UTC. Turn an n4445 slot list (K CSWAPs on wires 0..21, controls = linear forms of r43,r44,r45)
# into a patch_ops edit replacing original ops 186..217 (normalize levels 44+45), appended to edits/merge2.json.
# Region order (legal, checked by n4445_check.py on all x): ops 192-196, network (+ free CX on 43..45), restore 43..45, ops 213-215.
# Wire masks over (r43,r44,r45) at region start: q43=1, q44=3 (r44 := q44^q43), q45=4; required at end: q43=1, q44=2, q45=4.
# Usage: python3 n4445_build.py ops.json slots.log merge2.json out_edits.json
import json, sys, re, itertools
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
slots = [tuple(map(int, m.groups())) for l in open(sys.argv[2]) for m in [re.match(r'slot \d+ pair \((\d+), (\d+)\) form .* mask (\d+) const (\d+)', l)] if m]
assert all(c == 0 for *_, c in slots)
W3 = (43, 44, 45)
def bfs(start, goal):  # shortest CX sequence on wires 43..45; goal(state)->bool
    from collections import deque
    Q = deque([(start, [])]); seen = {start}
    while Q:
        s, p = Q.popleft()
        if goal(s): return s, p
        for i, j in itertools.permutations(range(3), 2):  # CX W3[i] -> W3[j]
            t = list(s); t[j] ^= t[i]; t = tuple(t)
            if t not in seen: seen.add(t); Q.append((t, p + [["CX", W3[i], W3[j], -1]]))
orig = lambda i: [K[ops[i][0]]] + ops[i][1:]
new = [orig(i) for i in range(192, 197)]
st = (1, 3, 4)
for a, b, f, _ in slots:
    st, p = bfs(st, lambda s: f in s); new += p
    new.append(["CSWAP", W3[st.index(f)], a, b, -1])
st, p = bfs(st, lambda s: s == (1, 2, 4)); new += p
new += [orig(i) for i in range(213, 216)]
E = json.load(open(sys.argv[3])) + [{"start": 186, "end": 218, "ops": new}]
json.dump(E, open(sys.argv[4], 'w'))
print('region ops', len(new), 'CSWAP', sum(o[0] == 'CSWAP' for o in new), 'CX', sum(o[0] == 'CX' for o in new))
