import numpy as np, sys, itertools
d = np.load(sys.argv[1]); xs, s, y = d['xs'], d['s'], d['y']; DL = int(sys.argv[2]) if len(sys.argv) > 2 else 1
F = 38
v0 = (y >> DL).astype(np.int64)
tgt = 1 / np.sqrt(xs.astype(np.float64)); tol = 2.0**-24 * tgt
def slack(jm):
    v = v0.copy()
    for r in range(4):
        m = 2**r; on = ((s >> r) & 1).astype(bool); j = jm[r]
        nv = (v & ((1 << j) - 1)) | ((v >> j) << (j + m))
        v = np.where(on, nv, v)
    ph = v.astype(np.float64) * 2.0**(DL - F)
    e = ph - tgt; e -= np.round(e)
    sl = tol - np.abs(e)
    i = int(np.argmin(sl)); return sl[i], xs[i]
base = slack([0, 0, 0, 0]); print('base', base)
for r in range(4):
    best = 0
    for j in range(1, 30):
        jm = [0]*4; jm[r] = j
        if slack(jm)[0] >= base[0] - 1e-30: best = j
        else: break
    print('stage', r, 'max jmin alone', best)
