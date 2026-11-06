"""For each free rotation k of an invsqrt circuit: fix its angle to the nearest Clifford+T value
(multiple of 1/8 turn; usually 0 = delete it) and re-fit the other angles by LP to maximise the
min margin. Reports the cost change: dropping a rotation saves its synthesis T count (~29 T = 7.2
Toffoli-eq) but the lower margin raises every remaining rotation's T count (0.56 log2 per halving).
Also reports rotations with identical / complementary firing patterns (could be merged).
Usage: python drop_rot.py trace.npz [k1,k2,...]
"""
import sys, math
import numpy as np
from scipy.optimize import linprog

z = np.load(sys.argv[1]); err = z['err'].astype(np.float64); tol = z['tol'].astype(np.float64)
I = z['I']; RU = z['rot_units'].astype(np.uint64)
nr, nx = I.shape
SC = 2.0**-30
e = err * SC; t = tol * SC
fired = I.astype(np.float64).sum(1)
print('n_rot', nr, 'mean fired/shot', I.sum(0).mean())
# identical / complementary patterns
for a in range(nr):
    for b in range(a + 1, nr):
        if np.array_equal(I[a], I[b]): print('IDENTICAL pattern', a, b)
        elif np.array_equal(I[a], 1 - I[b]): print('COMPLEMENT pattern', a, b)

def lp(fixed):
    """fixed: dict k -> delta (in SC units); returns min margin (SC units) after re-fit."""
    e0 = e.copy()
    for k, dk in fixed.items(): e0 = e0 + dk * I[k]
    free = [k for k in range(nr) if k not in fixed]
    m0 = t - np.abs(e0)
    act = set(np.argsort(m0)[:2000].tolist()) | set(np.random.default_rng(0).integers(0, nx, 5000).tolist())
    If = I[free].astype(np.float64)
    for it in range(40):
        idx = np.array(sorted(act)); A = If[:, idx].T
        Aub = np.vstack([np.hstack([A, np.ones((len(idx), 1))]), np.hstack([-A, np.ones((len(idx), 1))])])
        bub = np.concatenate([t[idx] - e0[idx], t[idx] + e0[idx]])
        c = np.zeros(len(free) + 1); c[-1] = -1
        res = linprog(c, A_ub=Aub, b_ub=bub, bounds=[(None, None)] * (len(free) + 1), method='highs')
        if res.status != 0: return -np.inf
        dl = res.x[:-1]; m = res.x[-1]
        e2 = e0 + dl @ If
        marg = t - np.abs(e2); viol = np.flatnonzero(marg < m - 1e-9)
        if len(viol) == 0 or m < 0: break
        act |= set(viol[np.argsort(marg[viol])[:3000]].tolist())
    return marg.min()

base = lp({})
nrot_shot = I.sum(0).mean()
def cost(margin_sc, nrot):
    eps = math.pi * (margin_sc / SC) / 2**64 / nrot
    return nrot * (0.56 * math.log2(1 / eps) + 5.3) / 4
c0 = cost(base, nrot_shot)
print(f'base margin {base / SC:.4g}  rot cost {c0:.2f} Toffoli-eq')
ks = [int(s) for s in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(nr)
for k in ks:
    u = int(RU[k]); q = 1 << 61  # 1/8 turn in 2^-64 units
    target = ((u + q // 2) // q) * q
    delta = ((target - u + (1 << 63)) % (1 << 64)) - (1 << 63)  # signed, units
    m = lp({k: delta * SC})
    if m <= 0:
        print(f'rot {k}: fires {fired[k] / nx:.4f}, angle {u / 2**64:.3e} turn -> {target / 2**64:.3f}: INFEASIBLE (margin {m / SC:.3g})', flush=True)
        continue
    nn = nrot_shot - fired[k] / nx
    c1 = cost(m, nn) + (fired[k] / nx) * (0.25 if target % (1 << 62) else 0)
    print(f'rot {k}: fires {fired[k] / nx:.4f}, margin {m / SC:.4g} ({m / base:.3f}x), cost {c1:.2f} vs {c0:.2f} -> {"GAIN" if c1 < c0 else "loss"} {c0 - c1:+.2f}', flush=True)
