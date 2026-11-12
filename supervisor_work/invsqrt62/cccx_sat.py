"""Exact SAT test: can the dirty-ancilla block  q19 ^= q28 q17 ; q25 ^= q28 q17 q19  (ops 25608..25614 / 28847..28853,
4 Toffolis, dirty q0 restored) be done with K Toffolis + arbitrary CNOT/X layers on n wires (n-5 extra dirty wires restored)?
Every affine layer is forced bijective because the whole map is a permutation. Usage: cccx_sat.py K n [timeout_s]"""
import sys, itertools, time
from pysat.solvers import Cadical153
from pysat.formula import IDPool
K = int(sys.argv[1]); n = int(sys.argv[2])
pool = IDPool(); cl = []
def v(*k): return pool.id(k)
T = pool.id(('true',)); cl.append([T])
def AND(a, b):
    z = pool.id(('and', a, b)); cl.extend([[-z, a], [-z, b], [z, -a, -b]]); return z
def XOR(a, b):
    z = pool.id(('xor', a, b)); cl.extend([[-z, a, b], [-z, -a, -b], [z, -a, b], [z, a, -b]]); return z
rows = list(itertools.product([0, 1], repeat=n))
def tgt(x):  # wires: 0 a=q28, 1 b=q17, 2 s=q19, 3 t=q25, 4 d=q0, 5.. extra dirty
    a, b, s, t = x[:4]; y = list(x); y[2] = s ^ (a & b); y[3] = t ^ (a & b & s); return y
# state literals
S = [[T if x[j] else -T for j in range(n)] for x in rows]
for L in range(K + 1):
    M = [[v('M', L, j, k) for k in range(n)] for j in range(n)]; c = [v('c', L, j) for j in range(n)]
    newS = []
    for r, x in enumerate(rows):
        out = []
        for j in range(n):
            acc = c[j]
            for k in range(n): acc = XOR(acc, AND(M[j][k], S[r][k]))
            out.append(acc)
        newS.append(out)
    if L < K:
        for r in range(len(rows)):
            newS[r][2] = XOR(newS[r][2], AND(newS[r][0], newS[r][1]))
        S = newS
    else:
        for r, x in enumerate(rows):
            y = tgt(x)
            for j in range(n): cl.append([newS[r][j] if y[j] else -newS[r][j]])
s = Cadical153(bootstrap_with=cl); t0 = time.time()
res = s.solve(); print(f'K={K} n={n} vars={pool.top} clauses={len(cl)} -> {"SAT" if res else "UNSAT"} ({time.time()-t0:.1f}s)')
