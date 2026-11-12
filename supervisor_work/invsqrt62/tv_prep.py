# Supervisor 2026-11-12 03:xx UTC. Convert a cswap_win_extract.py JSON into the transvection-SA input (cswap_win_tv.c):
# per case: control mask, then start and end value of every data wire as an affine mask (bit w = token d<data[w]>, bit W = const 1).
# Usage: python3 tv_prep.py win.json out.txt
import json, sys
J = json.load(open(sys.argv[1])); data = J['data']; W = len(data); idx = {f'd{w}': j for j, w in enumerate(data)}
def m(t): return 0 if t == 'z' else (1 << W) if t == 'o' else 1 << idx[t]
with open(sys.argv[2], 'w') as f:
    f.write(f"{W} {len(J['CTL'])} {len(J['cases'])}\n")
    for C in J['cases']:
        f.write(' '.join(map(str, [C['case']] + [m(t) for t in C['start']] + [m(t) for t in C['end']])) + '\n')
