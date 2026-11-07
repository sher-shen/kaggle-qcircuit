import numpy as np,sys
F=np.load('w/F.npy').astype(np.uint8)
def anf(t):
    t=t.copy()
    for i in range(8):
        s=1<<i
        for a in range(256):
            if a&s: t[a]^=t[a^s]
    return t
A=np.array([anf(f) for f in F])
H=[int(c) for c in sys.argv[1].split(',')];L=[i for i in range(8) if i not in H]
out=open(sys.argv[2],'w');terms=[]
for m in range(256):
    hi=sum(((m>>H[i])&1)<<i for i in range(4)); lo=sum(((m>>L[i])&1)<<i for i in range(4))
    if hi==0 or lo==0: continue
    c=sum(int(A[k,m])<<k for k in range(len(A)))
    if c: terms.append((1<<(hi-1),1<<(lo-1),c))
out.write(f"{len(terms)}\n"+''.join(f"{a} {b} {c}\n" for a,b,c in terms))
print(len(terms))
