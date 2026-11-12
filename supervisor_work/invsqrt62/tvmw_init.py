# Supervisor 2026-11-12 04:xx UTC. Turn ext22.py's original region (costly CSWAPs + free data CX + MU) into the tv22 model:
# K costly transvections, a split MU (index of the first gate after the measurement) and S (wires that get ^= z right before
# the HMR on wire 22).  Free CX gates are pushed right (conjugating later gates: P then T == T'' then P with
# L'' = P^T L, v'' = P^-1 v); at MU the accumulated P must be "CX 22 -> S" exactly.  Self-checked against ext22's targets.
# Usage: python3 tvmw_init.py x.txt x_gates.txt out_init.txt
# tvmw_init.py (supervisor 2026-11-12 06:xx UTC): row Z of P at MU may be any form Rz containing Z (free CX a->MW before
# the HMR: measured value z = <Rz, s>); S rows must be I[w] ^ Rz. Writes 'MU mu 0xS 0xRz'.
import sys
L0 = open(sys.argv[1]).read().split('\n'); W, NCT, NC = map(int, L0[0].split())
cases = []
for l in L0[1:1 + NC]:
    a = list(map(int, l.split())); cases.append((a[0], a[1:1 + W], a[1 + W:1 + 2 * W], a[1 + 2 * W]))
par = lambda x: bin(x).count('1') & 1
I = [1 << w for w in range(W)]
P = list(I); out = []; MU = None; Sm = 0; Z = W - 1  # wire 22 is the last data index
def inv(M):
    A = [(M[w], 1 << w) for w in range(W)]; R = [None] * W
    rows = list(A)
    for col in range(W):
        p = next(i for i in range(col, W) if rows[i][0] >> col & 1)
        rows[col], rows[p] = rows[p], rows[col]
        for i in range(W):
            if i != col and rows[i][0] >> col & 1: rows[i] = (rows[i][0] ^ rows[col][0], rows[i][1] ^ rows[col][1])
    return [rows[w][1] for w in range(W)]
for l in open(sys.argv[2]):
    t = l.split()
    if t[0] == 'MU':
        # P must be identity except row w ^= x22 for w in S, row 22 = x22
        RZ = P[Z]; assert RZ >> Z & 1
        for w in range(W):
            if P[w] == I[w] or w == Z: continue
            assert P[w] == I[w] ^ RZ, ('P at MU not of CX MW->S form', w, hex(P[w]))
            Sm |= 1 << w
        MU = len(out); P = list(I); continue
    Lm, v, f = int(t[0], 16), int(t[1], 16), int(t[2])
    if f == 0:  # free CX a->b: row b ^= row a
        a, b = Lm.bit_length() - 1, v.bit_length() - 1; P[b] ^= P[a]; continue
    Pi = inv(P); L2 = 0
    for w in range(W):
        if Lm >> w & 1: L2 ^= P[w]
    v2 = sum(1 << w for w in range(W) if par(Pi[w] & v))
    assert not par(L2 & v2); out.append((L2, v2, f))
assert P == I, 'free gates left after MU'
def ap(s, g, cs):
    Lm, v, f = g
    if not par(f & cs): return s
    a = 0
    for w in range(W):
        if Lm >> w & 1: a ^= s[w]
    return [s[w] ^ (a if v >> w & 1 else 0) for w in range(W)] if a else s
for cs, st, en, z in cases:
    s = list(st)
    for k, g in enumerate(out + [None]):
        if k == MU:
            zz = 0
            for w in range(W):
                if RZ >> w & 1: zz ^= s[w]
            assert zz == z, (cs, hex(zz), hex(z))
            s = [s[w] ^ (zz if Sm >> w & 1 else 0) for w in range(W)]; s[Z] = 0
        if g: s = ap(s, g, cs)
    assert s == en, cs
with open(sys.argv[3], 'w') as f:
    f.write(f'MU {MU} {hex(Sm)} {hex(RZ)}\n')
    for g in out: f.write(f'{hex(g[0])} {hex(g[1])} {g[2]}\n')
print('K', len(out), 'MU', MU, 'S', hex(Sm), 'RZ', hex(RZ), 'self-check OK on', NC, 'cases')
