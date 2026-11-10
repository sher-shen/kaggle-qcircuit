"""Don't-care pass over block_extract2.py's OPEN blocks: D = union of reachable entry patterns (block_reach.py, seeds given).
For each block: residue rank on D (block_rank.py criterion); if rank on D == 1 run k1_split (C brute force over all
hyperplanes, exact for K=1) on each non-affine output bit.  Usage: block_dset_k1.py ops.json k1_split_bin reach1.json [reach2.json]"""
import json, sys, subprocess
import numpy as np
from collections import Counter
here = __file__.rsplit('/', 1)[0] + '/'
opsf, k1bin, reachf = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.argv = ['x', opsf, '0', '0', '/dev/null']
exec(open(here + 'block_extract2.py').read().split('seen = {}')[0])
from block_rank import gf2_rank_mod
R = [json.load(open(f)) for f in reachf]; st = Counter()
for bi, b in enumerate(R[0]):
    D = sorted(set().union(*[set(r[bi]['reach']) for r in R])); n = len(b['W']); t = b['tof']
    if not D: st['empty'] += 1; continue
    _, y = perm_bits(b['W'], b['ops']); Y = y[np.asarray(D)].astype(np.int64)
    rows = [((Y >> j) & 1).astype(np.uint8) for j in range(n)]; rk, _ = gf2_rank_mod(D, n, rows)
    v = 'rankD=%d' % rk
    if rk == 1:
        hits = []
        for j in range(n):
            inp = '%d %d\n' % (n, len(D)) + ''.join('%d %d\n' % (p, (v_ >> j) & 1) for p, v_ in zip(D, Y.tolist()))
            out = subprocess.run([k1bin], input=inp, capture_output=True, text=True).stdout.strip().splitlines()[-1]
            if 'affine' not in out: hits.append(int(out.split()[-1]))
        v += ' k1 ' + ('NONE' if min(hits) == 0 else 'POSSIBLE')
    elif rk == 0: v += ' AFFINE-ON-D!'
    st[(t, b['rank'], v)] += 1
    if 'NONE' not in v or rk < b['rank']:
        print(bi, 'ops', b['ops'][0], b['ops'][-1], 'n', n, 'tof', t, 'rank', b['rank'], '|D|', len(D), v, flush=True)
for k, c in sorted(st.items(), key=str): print(k, c)
