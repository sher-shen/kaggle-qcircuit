"""Star 3->2 test (supervisor 2026-11-09 02 UTC): chain sum F = p_a + p_b + p_c (L=3 dump of chain_dump_scan) written as
F = v*w1 + u*w (+ affine, + relations K) with v one basis wire and w1, u, w arbitrary affine.  v*w1 = sum_i w1_i (v^e_i), so all
entries (v, i) become free: drop every pair containing v and run the exact rank<=2 block search (minrank_block.py) on the rest.
A hit gives a 3 -> 2 rewrite (CCX(v, w1, t) + CCX(u, w, t)); NONE(exact) closes that v.
Usage: [STAR2=1] star_scan.py dump.npz out_dir [v1,v2+v3,...]   (default: all vertices touched by a relation or by Q0)"""
import sys, os, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(sys.argv[1]); E = d['E']; P = d['pairs']; n = int(d['n']); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
touched = E[:, 1:].any(1) | E[:, 0].astype(bool)
vs = sorted({int(a) for t in np.nonzero(touched)[0] for a in P[t]})
vs = [(v,) for v in vs]
if os.environ.get('STAR2'):  # two stars: F = v1*w1 + v2*w2 + u*w  (L=4 -> 3)
    vs = [(a[0], b[0]) for i, a in enumerate(vs) for b in vs[i + 1:]]
if len(sys.argv) > 3: vs = [tuple(int(y) for y in x.split('+')) for x in sys.argv[3].split(',')]
base = os.path.basename(sys.argv[1])[:-4]
for v in vs:
    keep = np.array([int(a) not in v and int(b) not in v for a, b in P])
    fn = os.path.join(out, f"{base}_v{'+'.join(map(str, v))}.npz"); np.savez_compressed(fn, E=E[keep], pairs=P[keep], n=n)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'minrank_block.py'), fn], capture_output=True, text=True,
                       env=dict(os.environ, ORDER=os.environ.get('ORDER', 'auto2')))
    res = [l for l in r.stdout.splitlines() if 'RESULT' in l or 'n=' in l]
    print(base, 'v', '+'.join(map(str, v)), ' | '.join(res), r.stderr.strip()[-200:], flush=True)
    os.remove(fn); [os.remove(fn + s) for s in ('.txt',) if os.path.exists(fn + s)]
