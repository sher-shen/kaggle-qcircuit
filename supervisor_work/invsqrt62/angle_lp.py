"""Re-fit the free rotation angles of an invsqrt circuit to maximise the verifier's min margin
min_x (tol(x) - |err(x)|), which sets the rotation synthesis eps (eps ~ margin / n_rot).
err(x) is linear in the angles: err'(x) = err(x) + sum_k I[k, x] * delta_k.
Cutting-plane LP (HiGHS) over all x. Usage: python angle_lp.py trace.npz out_deltas.npy
"""
import sys
import numpy as np
from scipy.optimize import linprog

z = np.load(sys.argv[1]); err = z['err'].astype(np.float64); tol = z['tol'].astype(np.float64); I = z['I']
nr, nx = I.shape
SC = 2.0**-30  # scale units for conditioning
e = err * SC; t = tol * SC
marg0 = (t - np.abs(e)).min()
print('n_rot', nr, 'initial min margin (2^-64 turns)', marg0 / SC, 'worst ratio', (np.abs(e) / t).max())
act = set(np.argsort(t - np.abs(e))[:2000].tolist()) | set(np.random.default_rng(0).integers(0, nx, 5000).tolist())
for it in range(40):
    idx = np.array(sorted(act))
    A = I[:, idx].T.astype(np.float64)
    # vars: delta (nr), m ; maximise m
    #  A d + m <= t - e ;  -A d + m <= t + e
    Aub = np.vstack([np.hstack([A, np.ones((len(idx), 1))]), np.hstack([-A, np.ones((len(idx), 1))])])
    bub = np.concatenate([t[idx] - e[idx], t[idx] + e[idx]])
    c = np.zeros(nr + 1); c[-1] = -1
    res = linprog(c, A_ub=Aub, b_ub=bub, bounds=[(None, None)] * (nr + 1), method='highs')
    dl = res.x[:nr]; m = res.x[-1]
    e2 = e + I.T.astype(np.float64) @ dl if nx < 0 else e + (dl @ I.astype(np.float64) if False else np.einsum('k,kx->x', dl, I, dtype=np.float64))
    marg = t - np.abs(e2)
    viol = np.flatnonzero(marg < m - 1e-9)
    print(f'it {it} active {len(idx)} lp m {m / SC:.4g} true min margin {marg.min() / SC:.4g} viol {len(viol)}', flush=True)
    if len(viol) == 0: break
    act |= set(viol[np.argsort(marg[viol])[:3000]].tolist())
np.save(sys.argv[2], dl / SC)
print('final min margin', marg.min() / SC, 'gain x', marg.min() / marg0, 'worst ratio', (np.abs(e2) / t).max())
