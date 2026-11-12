# Supervisor 2026-11-12. GF(2) fit of a target wire's value as an affine function / a single product of two affine forms
# of the other wires, on samples.  fit_affine(F, y) -> coefficient vector or None.
import numpy as np
def gf2_solve(M, y):
    M = M.copy().astype(np.uint8); y = y.copy().astype(np.uint8); n, m = M.shape; piv = []; r = 0
    for c in range(m):
        p = np.nonzero(M[r:, c])[0]
        if len(p) == 0: continue
        p = p[0] + r; M[[r, p]] = M[[p, r]]; y[[r, p]] = y[[p, r]]
        rows = np.nonzero(M[:, c])[0]; rows = rows[rows != r]
        M[rows] ^= M[r]; y[rows] ^= y[r]; piv.append(c); r += 1
        if r == n: break
    if y[r:].any(): return None
    sol = np.zeros(m, np.uint8)
    for i, c in enumerate(piv): sol[c] = y[i]
    return sol
def fit_affine(F, y):
    """F: (nfeat, N) bool; y: (N,) bool. Returns coef over [const]+features or None. Uses unique rows."""
    X = np.vstack([np.ones(F.shape[1], bool), F]).T
    U, idx = np.unique(np.hstack([X, y[:, None]]), axis=0, return_index=True)
    return gf2_solve(U[:, :-1], U[:, -1])
