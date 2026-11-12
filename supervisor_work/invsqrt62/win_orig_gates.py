# Supervisor 2026-11-12. Dump the original CSWAPs of a pure window as SA init lines "a b form" (data indices, form over CTL bits).
# Usage: python3 win_orig_gates.py ops.json win.json out.txt
import json, sys
d = json.load(open(sys.argv[1])); K = d['kinds']; ops = d['ops']; J = json.load(open(sys.argv[2]))
m = {c: 1 << i for i, c in enumerate(J['CTL'])}; wi = {w: j for j, w in enumerate(J['data'])}
with open(sys.argv[3], 'w') as f:
    for i in range(J['A'], J['B']):
        o = ops[i]; k = K[o[0]]
        if k == 'CX': m[o[2]] ^= m[o[1]]
        else: f.write(f'{wi[o[2]]} {wi[o[3]]} {m[o[1]]}\n')
