# Supervisor 2026-11-12 02:xx UTC. Legal reorder of normalize levels 43..45 in p62m3.json so that 8 of the 10 level-43 CSWAPs
# (172-175, 179-181, 183: they touch neither 9/21/22 nor 13) sit next to the 44+45 network as one pure CSWAP window
# (controls 42..45 with only CX among them). Anchors 176-178 (wire-22 trick), 182 (touches 13) and 184-190 stay in front.
# Usage: python3 reorder434445.py p62m3.json out.json   -> prints window [A,B)
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; KI = {k: i for i, k in enumerate(K)}
assert all(K[ops[i][0]] == 'CSWAP' and ops[i][1] == 43 for i in (172, 173, 174, 175, 179, 180, 181, 182, 183))
cx = lambda a, b: [KI['CX'], a, b, -1]
mov = [172, 173, 174, 175, 179, 180, 181, 183]
front = [ops[i] for i in (176, 177, 178, 182)] + [ops[i] for i in range(184, 191)]
A = 172 + len(front)
win = [cx(42, 43)] + [ops[i] for i in mov] + [cx(42, 43)] + [ops[i] for i in range(191, 224)]
new = ops[:172] + front + win + ops[224:]
assert len(new) == len(ops) + 2
Z = d['zpow_exact']; assert all(int(k) < 172 or int(k) >= 224 for k in Z)
d['zpow_exact'] = {str(int(k) + (2 if int(k) >= 224 else 0)): v for k, v in Z.items()}
d['ops'] = new; d['n_ops'] = len(new); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[2], 'w'))
print('window', A, A + len(win))
