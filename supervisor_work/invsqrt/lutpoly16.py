"""lutpoly16 = lutpoly15 with an s-aware coefficient search (`--wsearch`).

The verifier's rotation budget is 2 pi min_x (tol(x) - |err(x)|) in *absolute* turns. For a
normalized x_norm = x 4^s that slack is proportional to 2^s (2^-24 exact_y - |y - exact_y|)
(y units), and the binding x for each x_norm is the smallest reachable s:
  s = 0 if x_norm <= MAX_X, s = 1 if x_norm > MAX_X and x_norm % 4 == 0, otherwise unreachable.
lutpoly7/calibrate centre a0 on the unweighted error over every x_norm in [2^20, 2^22) instead.
Here, per segment, (d1, d2) in [-R, R]^2 and the integer a0 shift are chosen to maximise
min_x 2^s (2^-24 exact - |err|) (ties: larger mean slack), then the usual clamp keeps y < 2^fy.
The circuit construction is unchanged.
"""
import os as _os, sys, math
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import numpy as np
import lutpoly15 as P15  # noqa: F401  (patches gadd in lutpoly14)
P = P15.P
MAX_X = P.MAX_X


def domain():
    xn = np.arange(2**20, 2**22, dtype=np.int64)
    s = np.where(xn <= MAX_X, 0, np.where(xn % 4 == 0, 1, -1))
    keep = s >= 0
    return xn[keep], s[keep]


class WSearch:
    R = 3
    DSH = 4

    def int_coefs(self):
        if getattr(self, '_opt', None) is not None:
            return [c.copy() for c in self._opt]
        c0 = P.Design.int_coefs(self)
        if getattr(self, '_searching', False):
            return c0
        self._searching = True
        saved = self.__dict__.pop('widths', None)
        xn, s = domain()
        exact = 2.0**self.fy / np.sqrt(xn / 2.0**20)
        tol = 2.0**-24 * exact
        w = 2.0**s
        A = xn >> self.D
        nseg = 2**self.k
        best = np.full(nseg, -np.inf); bd = np.zeros((nseg, 3), dtype=np.int64)
        R, DS = self.R, self.DSH
        for d1 in range(-R, R + 1):
            for d2 in range(-R, R + 1):
                c = [c0[0], c0[1] + d1, c0[2] + d2]
                try:
                    y = self.model(xn, c)
                except OverflowError:
                    continue
                err = self._drop(y, s) - exact
                lo = np.full(nseg, np.inf); hi = np.full(nseg, -np.inf)
                np.minimum.at(lo, A, err); np.maximum.at(hi, A, err)
                ok = np.isfinite(lo)
                cen = np.zeros(nseg, dtype=np.int64); cen[ok] = np.round((lo[ok] + hi[ok]) / 2).astype(np.int64)
                for dd in range(-DS, DS + 1):
                    sh = cen + dd
                    if getattr(self, 'droplane', False):  # the dropped bits depend on the shifted a0: re-drop
                        sl = w * (tol - np.abs(self._drop(y - sh[A], s) - exact))
                    else:
                        sl = w * (tol - np.abs(err - sh[A]))
                    m = np.full(nseg, np.inf); np.minimum.at(m, A, sl)
                    m[~ok] = -np.inf
                    upd = m > best + 1e-12
                    best[upd] = m[upd]; bd[upd, 0] = sh[upd]; bd[upd, 1] = d1; bd[upd, 2] = d2
        out = [c0[0] - bd[:, 0], c0[1] + bd[:, 1], c0[2] + bd[:, 2]]
        out[1] = np.maximum(out[1], 0); out[2] = np.maximum(out[2], 0)
        if saved is not None: self.widths = saved
        self._searching = False
        self._opt = out
        ok = np.isfinite(best)
        print(f'wsearch R={R}: min weighted slack {best[ok].min():.4f} (y units)', file=sys.stderr)
        return [c.copy() for c in out]

    def _drop(self, y, s):
        m = getattr(self, 'droprot', 0)  # --droprot m: lane bits < m (lane = y << s) are not phased
        if not m: return y
        if getattr(self, 'droplane', False):  # --droplane: y bits < m are dropped for every s
            return y - (y & ((1 << m) - 1))
        keep = np.where(m - s > 0, m - s, 0)
        return y - (y & ((1 << keep) - 1))

    def calibrate(self):
        xn = np.arange(2**20, 2**22, dtype=np.int64)
        coefs = self.int_coefs()
        A = xn >> self.D
        nseg = 2**self.k
        for _ in range(8):  # clamp: y < 2^fy
            y = self.model(xn, coefs)
            over = np.zeros(nseg, dtype=np.int64)
            np.maximum.at(over, A, y - (2**self.fy - 1))
            if over.max() <= 0: break
            coefs[0] = coefs[0] - over
        self.widths = [w - (1 if j == 0 else 0) for j, w in enumerate(self.widths)]
        self.coefs = coefs
        return self.max_rel_err()

    def slack_report(self, n_rot=35):
        xs = np.arange(1, MAX_X + 1, dtype=np.int64)
        s = (22 - (np.floor(np.log2(xs)).astype(np.int64) + 1)) // 2
        y = self._drop(self.model(xs << (2 * s), self.coefs), s).astype(np.float64)
        if _os.environ.get('DUMP_Y'): np.savez(_os.environ['DUMP_Y'], xs=xs, s=s, y=self.model(xs << (2 * s), self.coefs), fy=self.fy, w0=self.widths[0])
        approx = y * 2.0**(s - 10) / 2.0**self.fy
        tgt = 1 / np.sqrt(xs.astype(np.float64))
        err = np.abs(approx - tgt); tol = 2.0**-24 * tgt
        slack = tol - err
        i = int(np.argmin(slack)); r = float((err / tol).max())
        n_rot = n_rot - getattr(self, 'droprot', 0)
        if slack[i] <= 0:
            print(f'slack: FAIL worst err/tol {r:.5f} at x={xs[np.argmax(err/tol)]}', file=sys.stderr); return None
        eps = math.pi * 2 * slack[i] / (2 * n_rot)  # n_rot * 2 eps <= 2 pi slack (turns->rad: 2 pi)
        print(f'slack: worst err/tol {r:.5f}, min slack {slack[i]:.3e} turns at x={xs[i]}, eps~{eps:.3e}, '
              f'rot T each {0.56*math.log2(1/eps)+5.3:.3f}', file=sys.stderr)
        return eps


class SDesign(WSearch, P.Design):
    pass


if __name__ == '__main__':
    if '--R' in sys.argv:
        i = sys.argv.index('--R'); SDesign.R = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
    if '--droprot' in sys.argv:
        SDesign.droprot = int(sys.argv[sys.argv.index('--droprot') + 1])
    if '--droplane' in sys.argv:
        sys.argv.remove('--droplane'); SDesign.droplane = True
    if '--DSH' in sys.argv:
        i = sys.argv.index('--DSH'); SDesign.DSH = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
    if '--noclampw' in sys.argv: sys.argv.remove('--noclampw')
    _orig_cal = SDesign.calibrate
    def _cal(self):
        e = _orig_cal(self); self.slack_report(); return e
    SDesign.calibrate = _cal
    P.main(SDesign)
