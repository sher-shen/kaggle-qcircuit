import sys, math, itertools, dataclasses, time
import os as _os; ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/data/kickmix')
sys.path.insert(0, ROOT + '/data/verifiers/invsqrt')
import numpy as np
import nr_reference_circuit as nr
n_p = 10
max_x = 3 * (2**n_p - 2)**2
xs = np.arange(1, max_x + 1)
TOL = 2.0**-24

import variant
def cost(prec):
    c = variant.build(n_p, prec=prec, drop_square=DS, drop_horner=DH) if VARIANT else nr.build_nr_circuit(n_p, prec=prec)
    st = c.operation_statistics()
    return c.num_qubits, st.num_toffoli_like

def err(prec):
    try:
        return nr.relative_error(n_p, prec, xs).max()
    except OverflowError:
        return float('inf')

VARIANT = len(sys.argv) > 1
DS = DH = VARIANT
base = nr.Precision(*map(int, sys.argv[1].split(','))) if VARIANT else nr.Precision()
t=time.time(); print('base', cost(base), err(base)/TOL, time.time()-t, flush=True)

isq = 1/np.sqrt(xs.astype(np.float64))
cache = {}
def score(prec):
    k = dataclasses.astuple(prec)
    if k in cache: return cache[k]
    try:
        r = nr.relative_error(n_p, prec, xs)
    except (OverflowError, ValueError):
        cache[k] = (float('inf'),); return cache[k]
    if r.max() >= TOL:
        cache[k] = (float('inf'), r.max()/TOL); return cache[k]
    q, tof = cost(prec)
    nrot = prec.output_bits(n_p) - 3
    margin = ((TOL - r) * isq).min()          # turns
    eps = math.pi * margin / nrot
    C = tof + (1 + nrot * (0.56*math.log2(1/eps) + 5.3)) / 4
    cache[k] = (q*C, r.max()/TOL, q, tof, C)
    return cache[k]

cur = base; best = score(cur); print('start', best, flush=True)
names = [f.name for f in dataclasses.fields(nr.Precision)]
improved = True
while improved:
    improved = False
    for nm in names:
        for dv in (-1, -2, -3, 1):
            cand = dataclasses.replace(cur, **{nm: getattr(cur, nm) + dv})
            s = score(cand)
            print(' try', dataclasses.astuple(cand), s[:2], flush=True)
            if s[0] < best[0]:
                cur, best, improved = cand, s, True
                print('ACCEPT', dataclasses.astuple(cur), best, flush=True)
print('FINAL', cur, best)
