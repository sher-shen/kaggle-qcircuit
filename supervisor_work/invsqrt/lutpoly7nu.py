"""lutpoly7nu: lutpoly7 on top of lutpoly6nu (see lutpoly10.py).
lutpoly7 = lutpoly6 + per-segment integer local search of the Horner coefficients (b1, b2).

For every offset (d1, d2) in [-R, R]^2 the exact integer pipeline (same `model` as the circuit)
is run on every x_norm in [2^20, 2^22); per segment we keep the (b1+d1, b2+d2) whose relative
error spread (max - min, i.e. worst error after re-centring a0) is smallest. a0 is then
re-centred by the usual `calibrate`. The circuit construction is unchanged (lutpoly6/lutpoly4).
"""
import os as _os, sys, math
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import numpy as np
import lutpoly6nu as base


class Search:
    R = 3

    def search_domain(self):
        xn = np.arange(2**20, 2**22, dtype=np.int64)
        return xn, 2.0**self.fy / np.sqrt(xn / 2.0**20)

    def int_coefs(self):
        if getattr(self, '_opt', None) is not None:
            return [c.copy() for c in self._opt]
        c0 = super().int_coefs()
        if getattr(self, '_searching', False) or not getattr(self, 'search', False):
            return c0
        self._searching = True
        saved = self.__dict__.pop('widths', None)
        xn, exact = self.search_domain()
        A = base._seg(xn)
        nseg = 2**self.k
        best = np.full(nseg, np.inf); bd = np.zeros((nseg, 2), dtype=np.int64)
        R = self.R
        for d1 in range(-R, R + 1):
            for d2 in range(-R, R + 1):
                c = [c0[0], c0[1] + d1, c0[2] + d2]
                if (c[1] < 0).any() or (c[2] < 0).any():
                    pass
                y = self.model(xn, c)
                rel = (y - exact) / exact
                lo = np.full(nseg, np.inf); hi = np.full(nseg, -np.inf)
                np.minimum.at(lo, A, rel); np.maximum.at(hi, A, rel)
                spread = hi - lo
                upd = spread < best - 1e-15
                best[upd] = spread[upd]; bd[upd] = (d1, d2)
        out = [c0[0].copy(), c0[1] + bd[:, 0], c0[2] + bd[:, 1]]
        out[1] = np.maximum(out[1], 0); out[2] = np.maximum(out[2], 0)
        if saved is not None: self.widths = saved
        self._searching = False
        self._opt = out
        ok = np.isfinite(best)
        print(f'search R={R}: worst segment spread/2 2^{math.log2(best[ok].max() / 2):.2f}', file=sys.stderr)
        return [c.copy() for c in out]


class Design(Search, base.Design):
    pass


if __name__ == '__main__':
    Design.search = True
    if '--R' in sys.argv:
        i = sys.argv.index('--R'); Design.R = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
    base.main(Design)
