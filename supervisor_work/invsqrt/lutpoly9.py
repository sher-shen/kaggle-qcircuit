"""lutpoly9 = lutpoly7 restricted to the x_norm values the circuit can actually see.

x in [1, MAX_X] normalizes to x_norm = x 4^s in [2^20, 2^22). For s = 0 that is [2^20, MAX_X];
for s >= 1 only multiples of 4 occur. The (b1, b2) search and the a0 re-centring of lutpoly7 use
all of [2^20, 2^22); here both use only reachable x_norm (`--reach`), which frees some error
budget in the M in (MAX_X/2^20, 4) segments. Circuit construction unchanged.
"""
import os as _os, sys, math
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import numpy as np
import lutpoly6 as base
from lutpoly7 import Search


def reachable():
    xs = np.arange(1, base.MAX_X + 1, dtype=np.int64)
    s = (base.WIDTH - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
    return np.unique(xs << (2 * s))


class Design(Search, base.Design):
    def search_domain(self):
        xn = reachable()
        return xn, 2.0**self.fy / np.sqrt(xn / 2.0**20)

    def calibrate(self):
        orig = np.arange
        xr = reachable()
        def ar(*a, **k):  # base.calibrate builds arange(2^20, 2^22): swap in the reachable set
            if a[:2] == (2**20, 2**22): return xr.copy()
            return orig(*a, **k)
        base.np.arange = ar
        try:
            return base.Design.calibrate(self)
        finally:
            base.np.arange = orig


if __name__ == '__main__':
    Design.search = True
    if '--R' in sys.argv:
        i = sys.argv.index('--R'); Design.R = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
    base.main(Design)
