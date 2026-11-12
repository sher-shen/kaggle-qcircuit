# Supervisor 2026-11-12 05:xx UTC. Legal reorder of the unnormalize ladder in p62m5.json:
#  - CX block 46821-46823 (41^=15, 50^=15; reads control 15 only) moves in front of CSWAPs 46819/46820 (control 15 only, data
#    61,28,27,40 untouched by the block) -> commute.
#  - CSWAPs 46889-46891 (control 19, data 0..5) move in front of the wire-60 block 46879-46888 (touches 60,16,17,40,41,6 and
#    CZ(19,6), CZ(19,41) which are diagonal on the CSWAP control) -> commute.
# Result: pure CSWAP window [46822, 46882) of the output = 52 CSWAPs (+ CX among controls 15,18,14,16,19).
# Usage: python3 reorder_unnorm.py p62m5.json out.json
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
assert [K[ops[i][0]] for i in (46819, 46820, 46889, 46890, 46891)] == ['CSWAP'] * 5
assert all(K[ops[i][0]] == 'CX' for i in (46821, 46822, 46823))
blk = ops[46879:46889]
for o in blk: assert not (set(o[1:-1]) & {0, 1, 2, 3, 4, 5}), o
new = ops[:46819] + ops[46821:46824] + ops[46819:46821] + ops[46824:46879] + ops[46889:46892] + blk + ops[46892:]
assert len(new) == len(ops)
Z = d['zpow_exact']; assert all(int(k) < 46819 or int(k) >= 46892 for k in Z)
d['ops'] = new; d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[2], 'w'))
print('window', 46822, 46882)
