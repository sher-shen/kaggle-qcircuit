"""Run block_peel2 on every OPEN block (block_extract2 output + block_reach 'reach' + add_perm 'perm').
For each block: rank r on D (root of block_peel2).  If r == tof-1 the search with K = tof-1 is exact (NONE closes
tof -> tof-1 on D).  r < tof-1 is reported as SLACK (not decided).  Usage: block_peel2_all.py ab_enum_bin blocks.json"""
import sys, json, time
from collections import Counter
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import block_peel2 as P2
abbin = sys.argv[1]; B = json.load(open(sys.argv[2])); st = Counter()
for bi, b in enumerate(B):
    n = len(b['W']); t = b['tof']; Dx = b['reach']
    if not Dx: st['empty'] += 1; continue
    t0 = time.time(); m, h, sl = P2.run(b['perm'], n, Dx, t - 1, abbin)
    v = 'HIT' if h else ('SLACK(rankD<t-1)' if sl else 'NONE(exact)')
    st[(t, v)] += 1
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', t, 'rank', b['rank'], '|D|', len(Dx), 'hull', m,
          'nodes', P2.stats['nodes'], '%.1fs' % (time.time() - t0), v, h[0] if h else '', flush=True)
for k, c in sorted(st.items(), key=str): print(k, c)
