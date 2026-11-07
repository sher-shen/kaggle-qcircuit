import numpy as np
F=np.load('w/F.npy').astype(np.uint8)
def anf(t):
    t=t.copy()
    for i in range(8):
        s=1<<i
        for a in range(256):
            if a&s: t[a]^=t[a^s]
    return t
A=np.array([anf(f) for f in F])
pc=np.array([bin(a).count('1') for a in range(256)])
print('n outputs',len(F))
for k,a in enumerate(A): print(k,'deg',pc[a==1].max() if a.any() else -1,'terms',a.sum())
U=A.any(0); print('union monomials',U.sum(),'nonlinear',(U&(pc>=2)).sum())
r=np.linalg.matrix_rank
# GF2 rank of outputs mod affine
def gf2rank(M):
    M=M.copy()%2;r=0;rows,cols=M.shape
    for c in range(cols):
        p=[i for i in range(r,rows) if M[i,c]]
        if not p: continue
        M[[r,p[0]]]=M[[p[0],r]]
        for i in range(rows):
            if i!=r and M[i,c]: M[i]^=M[r]
        r+=1
    return r
print('rank of ANF restricted to deg>=2',gf2rank(A[:,pc>=2]))
