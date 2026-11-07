"""Scan (a, LA) for lutpoly14 --groups on V's settings: smallest LA whose window never wraps, and the
static Toffoli change per direction (rows i<a: (LA+2-lo)-1 instead of (L+2-lo)-1; fold A: L-LA+1)."""
import sys
sys.argv = ['x', '--topccx']
import lutpoly14 as P
D = P.SDesign; D.search = True; D.round = (1, 2)
d = D(9, 2, 28, guards=[0, -2, -4], binshift=True, rangeq=True, packflags=True)
d.clamp = True; d.calibrate(); Ls = d.choose_L(); print('L', Ls)
for j in (1, 2):
    L = Ls[j]; sh = d.guards[j] - d.guards[j - 1]; m = d.widths[j] - 0
    for a in range(1, d.D):
        for LA in range(1, L):
            ok, lo_, hi_ = P.group_ok(d, j, a, LA)
            if ok: break
        else: continue
        save = 0
        for i in range(a):
            e = i - d.D - sh
            terms = [q + e for q in range(m) if 0 <= q + e < L + 2]
            if not terms: continue
            lo = terms[0]
            save += (L + 2 - lo - 1) - max(0, (LA + 2 - lo - 1))
        fold = (L - LA + 2) - 1
        print(f'j={j} a={a} LA={LA} range[{lo_},{hi_}] save/dir {save} foldA {fold} net/dir {save - fold}')
