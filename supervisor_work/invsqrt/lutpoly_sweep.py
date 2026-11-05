import sys, math, itertools
sys.path.insert(0, __import__('os').path.dirname(__file__))
from lutpoly import Design
REF = 2076774.23
res = []
for k, deg in [(9, 2), (8, 2), (7, 3), (6, 3), (5, 4), (8, 3), (7,2)]:
    for fy in range(27, 33):
        for g in (0, 1, 2, 3):
            d = Design(k, deg, fy, guards=[0] + [g] * deg)
            e = d.calibrate()
            if e > 2**-24.6:
                continue
            c = d.build()
            q, t = c.num_qubits, c.operation_statistics().num_toffoli_like
            C = t + 240
            res.append((q * C, k, deg, fy, g, q, t, math.log2(e)))
            break
res.sort()
for r in res[:15]:
    print(f'est {REF/r[0]:.2f}x  k={r[1]} deg={r[2]} fy={r[3]} g={r[4]} Q={r[5]} T={r[6]} err=2^{r[7]:.2f}')
