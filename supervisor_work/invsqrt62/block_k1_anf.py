"""Exact K=1 test for rank-1 blocks of any n <= ~22 (full domain), complementing block_extract2.py.
If P = A2 o g o A1 (one Toffoli/CSWAP), every output bit is affine + c_j * a(x) b(x) with a, b affine in x.  So every output
bit's ANF has degree <= 2 and the degree-2 part (an alternating form) has rank <= 2 and is the same form for all bits with c_j=1.
Test: ANF (Moebius transform) of every output bit; NONE(exact) if some bit has degree > 2 or a quadratic part of rank > 2.
Usage: block_k1_anf.py ops.json opened.json   (opened.json from block_extract2.py; only rank-1 blocks are tested)"""
import json, sys
import numpy as np
sys.argv_ = sys.argv
ops_file, op_file = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], ops_file, '0', '0', '/dev/null']
# reuse info / perm_bits from block_extract2 without running its scan
src = open(__file__.replace('block_k1_anf.py', 'block_extract2.py')).read().split('seen = {}')[0]
exec(src)
def anf(bits, n):
    a = bits.astype(np.uint8).copy()
    for i in range(n):
        a = a.reshape(-1, 2, 1 << i); a[:, 1, :] ^= a[:, 0, :]; a = a.reshape(-1)
    return a
def gf2rank(M):
    M = M.copy() % 2; r = 0; rows, cols = M.shape
    for c in range(cols):
        p = [i for i in range(r, rows) if M[i, c]]
        if not p: continue
        M[[r, p[0]]] = M[[p[0], r]]
        for i in range(rows):
            if i != r and M[i, c]: M[i] ^= M[r]
        r += 1
    return r
pc = np.array([bin(i).count('1') for i in range(1 << 20)], np.uint8)
for b in json.load(open(op_file)):
    if b['rank'] != 1: continue
    n, y = perm_bits(b['W'], b['ops']); deg = 0; qr = 0; forms = set()
    for j in range(n):
        a = anf((y >> np.uint32(j)) & np.uint32(1), n); idx = np.flatnonzero(a)
        dj = int(pc[idx].max()) if len(idx) else 0; deg = max(deg, dj)
        q = [m for m in idx if pc[m] == 2]
        if q:
            M = np.zeros((n, n), np.uint8)
            for m in q:
                u, v = [k for k in range(n) if (m >> k) & 1]; M[u, v] = M[v, u] = 1
            qr = max(qr, gf2rank(M)); forms.add(tuple(sorted(int(m) for m in q)))
    v = 'NONE(exact)' if deg > 2 or qr > 2 or len(forms) > 1 else 'PASS-necessary'
    print('n %d tof %d ops %d..%d maxdeg %d max-quad-rank %d forms %d -> %s' % (n, b['tof'], b['ops'][0], b['ops'][-1], deg, qr, len(forms), v), flush=True)
