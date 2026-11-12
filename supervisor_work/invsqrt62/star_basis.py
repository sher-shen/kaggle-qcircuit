"""Star 3->2 with a general centre (supervisor 2026-11-09 04 UTC, instruction 2 of 03:10).
star_scan.py only allows the star centre v to be one basis wire.  Here v = sum_{c in S} x_c (any GF(2) combination of basis
wires): change basis x = M x' with x'_{c0} = v (c0 = min S), so every alternating form A becomes M^T A M; then v is basis
vertex c0 and the star test is the same as in star_scan.py (drop all pairs containing c0, exact rank<=2 block search).
Usage: star_basis.py dump.npz out_dir COMBOS
  COMBOS: 'ctrl2' = all |S|>=2 subsets of the vertices given by CTRL (default 0,1,2,3: the dump puts the last CCX pair's
  control values first), 'pairs' = all weight-2 combos of the touched block, or an explicit list like 0+1,2+5+7.
[PLANT=1: plant v*w1 + u*w with v = the first combo before testing (self-test, must HIT).]"""
import sys, os, itertools, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
d = np.load(sys.argv[1]); E0 = d['E'].astype(np.uint8); P = d['pairs']; n = int(d['n']); out = sys.argv[2]
os.makedirs(out, exist_ok=True); base = os.path.basename(sys.argv[1])[:-4]
iu = np.triu_indices(n, 1)
assert len(P) == len(iu[0]) and (P[:, 0] == iu[0]).all() and (P[:, 1] == iu[1]).all()
def to_mats(E):
    A = np.zeros((E.shape[1], n, n), np.uint8); A[:, iu[0], iu[1]] = E.T; A[:, iu[1], iu[0]] = E.T; return A
A0 = to_mats(E0)
touched = E0[:, 1:].any(1) | E0[:, 0].astype(bool)
blk = sorted({int(a) for t in np.nonzero(touched)[0] for a in P[t]})
spec = sys.argv[3]
if spec == 'ctrl2':
    C = [int(x) for x in os.environ.get('CTRL', '0,1,2,3').split(',')]
    combos = [S for r in range(2, len(C) + 1) for S in itertools.combinations(C, r)]
elif spec == 'pairs': combos = list(itertools.combinations(blk, 2))
else: combos = [tuple(sorted(int(y) for y in x.split('+'))) for x in spec.split(',')]
rng = np.random.default_rng(7)
for S in combos:
    c0 = S[0]; M = np.eye(n, dtype=np.uint8)
    for c in S[1:]: M[c0, c] = 1
    A = (np.einsum('ji,cjk,kl->cil', M.astype(np.int64), A0.astype(np.int64), M.astype(np.int64)) & 1).astype(np.uint8)
    assert not A[:, np.arange(n), np.arange(n)].any()
    E = A[:, iu[0], iu[1]].T.copy()
    if os.environ.get('PLANT'):
        w1, u, w = (rng.random((3, n)) < 0.3).astype(np.uint8); l = (rng.random(E.shape[1] - 1) < 0.5).astype(np.uint8)
        for t, (a, b) in enumerate(P):  # v = e_c0 in the new basis
            va = int(a == c0); vb = int(b == c0)
            E[t, 0] = (va * w1[b] ^ vb * w1[a] ^ u[a] * w[b] ^ u[b] * w[a] ^ (int(E[t, 1:] @ l) & 1)) & 1
    keep = np.array([int(a) != c0 and int(b) != c0 for a, b in P])
    fn = os.path.join(out, f"{base}_S{'+'.join(map(str, S))}.npz"); np.savez_compressed(fn, E=E[keep], pairs=P[keep], n=n)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'minrank_block.py'), fn], capture_output=True, text=True,
                       env=dict(os.environ, ORDER=os.environ.get('ORDER', 'auto2')))
    res = [l for l in r.stdout.splitlines() if 'RESULT' in l or 'n=' in l]
    print(base, 'S', '+'.join(map(str, S)), ' | '.join(res), r.stderr.strip()[-200:], flush=True)
    os.remove(fn); [os.remove(fn + s) for s in ('.txt',) if os.path.exists(fn + s)]
    if os.environ.get('PLANT'): break
