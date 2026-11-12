"""deg-3 coefficient search harness for lutpoly11 (the lutpoly7 search only handles deg 2). Usage: deg3_search.py K FY "g0,g1,g2,g3;..."."""
import sys, math, io, contextlib, itertools
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import lutpoly11 as L
class S3(L.Design):
    R = 2
    search = True
    def int_coefs(self):
        if getattr(self, '_opt', None) is not None:
            return [c.copy() for c in self._opt]
        c0 = super().int_coefs()
        if getattr(self, '_searching', False): return c0
        self._searching = True
        saved = self.__dict__.pop('widths', None)
        xn = np.arange(2**20, 2**22, dtype=np.int64); exact = 2.0**self.fy/np.sqrt(xn/2.0**20)
        A = xn >> self.D; nseg = 2**self.k
        best = np.full(nseg, np.inf); bd = np.zeros((nseg, self.deg), dtype=np.int64)
        R = self.R
        for ds in itertools.product(range(-R, R+1), repeat=self.deg):
            c = [c0[0]] + [c0[j] + ds[j-1] for j in range(1, self.deg+1)]
            y = self.model(xn, c)
            rel = (y - exact)/exact
            lo = np.full(nseg, np.inf); hi = np.full(nseg, -np.inf)
            np.minimum.at(lo, A, rel); np.maximum.at(hi, A, rel)
            sp = hi - lo; upd = sp < best - 1e-15
            best[upd] = sp[upd]; bd[upd] = ds
        out = [c0[0].copy()] + [np.maximum(c0[j] + bd[:, j-1], 0) for j in range(1, self.deg+1)]
        if saved is not None: self.widths = saved
        self._searching = False; self._opt = out
        return [c.copy() for c in out]
def run(k, deg, fy, guards, rnd, R=2, build=True):
    class D(S3): pass
    D.R = R; D.round = rnd
    d = D(k, deg, fy, guards=list(guards), rangeq=True, packflags=True)
    d.pad=0; d.clamp=d.binnorm=d.zshift=d.droptop=d.smallfirst=d.foldadd=d.gadd=True; d.maxq=0; d.droprot=0
    e = d.calibrate()
    if not build or math.log2(e) > -23.95: return e, None, None, d
    d.choose_L(); c = d.build()
    return e, c.num_qubits, c.operation_statistics().num_toffoli_like, d
if __name__ == '__main__':
    k=int(sys.argv[1]); fy=int(sys.argv[2])
    for g in sys.argv[3].split(';'):
        gs = tuple(int(v) for v in g.split(','))
        for rnd in [(1,2,3),(1,2),(1,)]:
            try:
                e,Q,T,d = run(k, 3, fy, gs, rnd)
                print(k,fy,gs,rnd,f'err 2^{math.log2(e):.3f}', d.widths, Q, T, Q*(T+262) if Q else None, flush=True)
            except Exception as ex:
                print(k,fy,gs,rnd,'ERR',type(ex).__name__,ex, flush=True)
