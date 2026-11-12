# Supervisor 2026-11-11. Apply a SAT slot list (n4445_sat.py output) to the real start state of all 3,133,453 x
# and compare wires 0..21 with the original circuit's state after the region (see n4445_sat_extract.py).
# Usage: python3.13 n4445_check.py p62mm.json sat_output.log
import json, sys, re, numpy as np
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']
N = 3133453; X = np.arange(N, dtype=np.int64)
q = np.zeros((64, N), dtype=bool)
for j in range(22): q[j] = (X >> j) & 1
def ap(i):
    o = ops[i]; k = K[o[0]]
    if k == 'CSWAP': c, a, b = o[1], o[2], o[3]; m = q[c] & (q[a] ^ q[b]); q[a] ^= m; q[b] ^= m
    elif k == 'X': q[o[1]] ^= True
    elif k == 'CX': q[o[2]] ^= q[o[1]]
    elif k == 'CCX': q[o[3]] ^= q[o[1]] & q[o[2]]
    elif k in ('HMR', 'R'): q[o[1]] = False
for i in range(186): ap(i)
for i in range(192, 197): ap(i)
r = [q[43].copy(), q[44] ^ q[43], q[45].copy()]
st = q[:22].copy()
for i in list(range(186, 192)) + [197, 198, 199, 200, 201] + list(range(202, 213)) + [216, 217]: ap(i)
end = q[:22].copy(); s = st
n = 0
for line in open(sys.argv[2]):
    m = re.match(r'slot \d+ pair \((\d+), (\d+)\) form .* mask (\d+) const (\d+)', line)
    if not m: continue
    a, b, f, c = map(int, m.groups()); n += 1
    ctl = np.zeros(N, dtype=bool) ^ bool(c)
    for i in range(3):
        if (f >> i) & 1: ctl ^= r[i]
    mm = ctl & (s[a] ^ s[b]); s[a] ^= mm; s[b] ^= mm
print('slots', n, 'match all x:', bool(np.array_equal(s, end)), 'mismatching x:', int((s != end).any(0).sum()))
