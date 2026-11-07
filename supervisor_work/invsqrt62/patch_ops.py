"""Apply range-replacement edits to an ops.json, remapping zpow_exact keys (op-index keyed).

Usage: python patch_ops.py in.json edits.json out.json
edits.json: list of {"start": i, "end": j, "ops": [[kind_name, args...], ...]} on ORIGINAL indices
(non-overlapping), replacing ops[i:j]; kind names as in d['kinds']. A Z_POW op may be kept by giving
["KEEP", orig_index]. New HMR bits must be < n_bits or n_bits is raised.
"""
import json, sys
d = json.load(open(sys.argv[1])); E = sorted(json.load(open(sys.argv[2])), key=lambda e: e['start'])
K = d['kinds']; KI = {k: i for i, k in enumerate(K)}; Z = d['zpow_exact']
new_ops, newZ, pos = [], {}, 0
def keep(i):
    o = d['ops'][i]
    if str(i) in Z: newZ[str(len(new_ops))] = Z[str(i)]
    new_ops.append(o)
maxbit = d['n_bits'] - 1
for e in E:
    assert e['start'] >= pos
    for i in range(pos, e['start']): keep(i)
    for o in e['ops']:
        if o[0] == 'KEEP': keep(o[1]); continue
        o2 = [KI[o[0]]] + o[1:]
        if o[0] == 'HMR': maxbit = max(maxbit, o[2])
        new_ops.append(o2)
    pos = e['end']
for i in range(pos, len(d['ops'])): keep(i)
d['ops'] = new_ops; d['zpow_exact'] = newZ; d['n_ops'] = len(new_ops); d['n_bits'] = maxbit + 1
d.pop('source_kmb_sha256', None)
json.dump(d, open(sys.argv[3], 'w'))
print('ops', len(new_ops), 'n_bits', d['n_bits'])
