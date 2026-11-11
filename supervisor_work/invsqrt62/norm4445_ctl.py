import json, sys, numpy as np
d=json.load(open(sys.argv[1])); K=d['kinds']
X=np.arange(0,3133453,dtype=np.int64); N=len(X)
q=np.zeros((64,N),dtype=bool)
for j in range(22): q[j]=(X>>j)&1
snaps={}
for i in range(0,240):
    if i in (144,158,172,186,202,218): snaps[i]=q.copy()
    o=d['ops'][i]; k=K[o[0]]
    if k=='CSWAP':
        c,a,b=o[1],o[2],o[3]; m=q[c]&(q[a]^q[b]); q[a]^=m; q[b]^=m
    elif k=='X': q[o[1]]^=True
    elif k=='CX': q[o[2]]^=q[o[1]]
    elif k=='CCX': q[o[3]]^=q[o[1]]&q[o[2]]
    elif k in ('HMR','R'): q[o[1]]=False
s=snaps[144]
c={w:s[w] for w in (42,43,44,45,46)}
import itertools
key=sum(c[w].astype(int)<<i for i,w in enumerate((46,42,43,44,45)))
u,n=np.unique(key,return_counts=True)
for a,b in zip(u,n): print('ctl(46,42,43,44,45)=',[(a>>i)&1 for i in range(5)],b)
np.save(sys.argv[2],np.stack([snaps[k] for k in sorted(snaps)]))
