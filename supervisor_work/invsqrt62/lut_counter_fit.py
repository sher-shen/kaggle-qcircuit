import sys,numpy as np
F=np.load(sys.argv[1]).astype(np.int64); W=[22,24]+list(range(29,62)); idx={w:i for i,w in enumerate(W)}
for name,top in (('A',[41,57,40,51,50]),('B',[60,44,43,59,24,42])):
    n=len(top); M=1<<n
    v=np.zeros(256,np.int64)
    for w in top: v=2*v+F[idx[w]]
    for h in (0,1):
        s=v[h*128:(h+1)*128].copy()
        s=np.where(s>=M//2,s-M,s)  # signed
        x=np.arange(128)
        print(name,h,'signed range',s.min(),s.max(),'d2 uniq',np.unique(np.diff(s,2)))
        for deg in (1,2,3):
            p=np.polyfit(x,s,deg); r=s-np.polyval(p,x); print('   deg',deg,'coef',np.round(p,5),'max resid %.2f'%np.abs(r).max())
