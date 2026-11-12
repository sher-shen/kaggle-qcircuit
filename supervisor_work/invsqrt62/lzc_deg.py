# Degree of the leading-zero-count bits of a 22-bit x restricted to x21=0 (all x<2^21 are in the invsqrt domain).
import numpy as np
n=21; X=np.arange(1<<n,dtype=np.int64)
L=np.full(X.shape,22); nz=X>0
L[nz]=22-np.floor(np.log2(X[nz])).astype(int)-1  # leading zeros in 22-bit word
for b in range(5):
    f=((L>>b)&1).astype(np.uint8)
    a=f.copy()
    for i in range(n):
        a=a.reshape(-1,2,1<<i); a[:,1,:]^=a[:,0,:]; a=a.reshape(-1)
    idx=np.nonzero(a)[0]; deg=max(bin(int(v)).count('1') for v in idx)
    print('c%d degree on x21=0 cube:'%b,deg,'-> MC >=',deg-1)
