import numpy as np,itertools
F=np.load('w/F.npy').astype(np.uint8)
def anf(t):
    t=t.copy()
    for i in range(8):
        s=1<<i
        for a in range(256):
            if a&s: t[a]^=t[a^s]
    return t
A=np.array([anf(f) for f in F])  # 35x256 monomial coeffs
def gf2rank(M):
    M=M.copy()%2;r=0;rows,cols=M.shape
    for c in range(cols):
        p=np.nonzero(M[r:,c])[0]
        if len(p)==0: continue
        p=p[0]+r
        M[[r,p]]=M[[p,r]]
        idx=np.nonzero(M[:,c])[0]; idx=idx[idx!=r]
        M[idx]^=M[r]; r+=1
        if r==rows: break
    return r
def tensor(H):
    L=[i for i in range(8) if i not in H]
    T=np.zeros((16,16,len(A)),np.uint8)
    for m in range(256):
        hi=sum(((m>>H[i])&1)<<i for i in range(4)); lo=sum(((m>>L[i])&1)<<i for i in range(4))
        T[hi,lo]=A[:,m]
    return T
res=[]
for H in itertools.combinations(range(8),4):
    if 0 not in H: continue
    T=tensor(H)[1:,1:]
    r1=sum(gf2rank(T[j]) for j in range(15)); r2=sum(gf2rank(T[:,j]) for j in range(15))
    flat=[gf2rank(T.reshape(15,-1)),gf2rank(T.transpose(1,0,2).reshape(15,-1)),gf2rank(T.transpose(2,0,1).reshape(35,-1))]
    res.append((min(r1,r2),H,r1,r2,flat))
res.sort()
for r in res[:8]: print(r)
print('worst',res[-1])
