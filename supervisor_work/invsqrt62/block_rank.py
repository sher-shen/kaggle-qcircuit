"""Residue-rank bound for block rewrites (any K, any n; instruction 2 of SUPERVISOR 11-10 22:00, generalised).
Claim: if P|D = (g_K ... g_1 A)|D with each g_i a Toffoli-class gate (CCX / CSWAP; x -> x + v_i f_i(x)) and A affine, then every
output bit of P is (affine on D) + sum_i c_i f_i'(x), where f_i' = f_i composed with the earlier layers.  So modulo
V = {affine functions restricted to D}, the residues of the n output bits span a space of dimension <= K.
Hence rank(residues of P on D) >= t  =>  no rewrite of the block with <= t-1 Toffolis on the same wires (with D as don't-cares).
The original block (t Toffolis) always has rank <= t (checked: rank > t would be a bug).
Usage: block_rank.py blocks.json [reach1.json reach2.json ...]   (no reach file -> full domain)"""
import sys, json, numpy as np
from collections import Counter
def gf2_rank_mod(D, n, rows):
    """rank of `rows` (bit-vectors over D) modulo span{1, x_0..x_{n-1}} restricted to D"""
    Dn = np.asarray(D, np.int64)
    aff = [np.ones(len(D), np.uint8)] + [((Dn >> j) & 1).astype(np.uint8) for j in range(n)]
    B = []; piv = []
    def reduce(r):
        r = r.copy()
        for b, p in zip(B, piv):
            if r[p]: r ^= b
        return r
    for r in aff:
        r = reduce(r); nz = np.flatnonzero(r)
        if len(nz): B.append(r); piv.append(nz[0])
    base = len(B); rk = 0
    for r in rows:
        r = reduce(r); nz = np.flatnonzero(r)
        if len(nz): B.append(r); piv.append(nz[0]); rk += 1
    return rk, base
if __name__ == '__main__':
    blocks = json.load(open(sys.argv[1])); reach = [json.load(open(f)) for f in sys.argv[2:]]
    st = Counter(); bad = 0
    for bi, b in enumerate(blocks):
        n = len(b['W']); t = b['tof']
        if reach:
            D = sorted(set().union(*[set(rr[bi]['reach']) for rr in reach]))
            if not D: st[(n, t, 'empty-D')] += 1; continue
        else:
            D = list(range(1 << n))
        P = np.asarray(b['perm'], np.int64)[np.asarray(D)]
        rows = [((P >> j) & 1).astype(np.uint8) for j in range(n)]
        rk, dimV = gf2_rank_mod(D, n, rows)
        if rk > t: bad += 1; v = 'BUG(rank>t)'
        elif rk >= t: v = 'NONE(rank=t)'
        else: v = 'OPEN(rank=%d)' % rk
        st[(n, t, v)] += 1
        if not v.startswith('NONE'):
            print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'W', b['W'], 'tof', t, '|D|', len(D), 'dimV', dimV, v, flush=True)
    for k in sorted(st): print('n %d tof %d %s: %d' % (k + (st[k],)))
    print('total', sum(st.values()), 'bugs', bad)
