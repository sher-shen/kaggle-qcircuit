# Supervisor 2026-11-12 06:xx UTC. Legal reorder of p62u (reorder_unnorm.py output) for the wire-60 unnormalize model:
# X 60 (46882) and CX 16->60 (46883) move to just before the wu52 window (46822). Legal: wire 60 is untouched in
# [46822, 46882) and control wire 16 has the same value at 46822 and 46883 (the only writes are CX 19->16 at 46860 and 46871,
# with 19 unchanged in between). Usage: python3 prep60.py p62u.json p62u60.json
import json, sys
d = json.load(open(sys.argv[1])); ops = d['ops']; K = d['kinds']
assert ops[46882] == [K.index('X'), 60, -1] and ops[46883] == [K.index('CX'), 16, 60, -1]
for i in range(46822, 46882): assert 60 not in ops[i][1:-1], i
w16 = [i for i in range(46822, 46883) if K[ops[i][0]] in ('CX',) and ops[i][2] == 16]
assert w16 == [46860, 46871] and all(19 not in ops[i][2:3] for i in range(46860, 46871) if K[ops[i][0]] == 'CX'), w16
mv = [ops[46882], ops[46883]]
new = ops[:46822] + mv + ops[46822:46882] + ops[46884:]
Zp = d['zpow_exact']; assert all(int(k) < 46822 or int(k) >= 46884 for k in Zp)
d['ops'] = new; d['n_ops'] = len(new); d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[2], 'w')); print('ok, window now', 46824, 46892)
