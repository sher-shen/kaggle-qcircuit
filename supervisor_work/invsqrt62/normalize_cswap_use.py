import json, sys, numpy as np
d=json.load(open(sys.argv[1])); K=d['kinds']; a,b=int(sys.argv[2]),int(sys.argv[3])
X=np.arange(0,3133453,dtype=np.int64)
q=np.zeros((64,len(X)),dtype=bool)
for j in range(22): q[j]=(X>>j)&1
for i in range(a,b):
    o=d['ops'][i]; k=K[o[0]]
    if k=='X': q[o[1]]^=True
    elif k=='CX': q[o[2]]^=q[o[1]]
    elif k=='CCX': 
        t=q[o[1]]&q[o[2]]; 
        if not t.any(): print('CCX never fires',i)
        q[o[3]]^=t
    elif k=='CSWAP':
        m=q[o[1]]&(q[o[2]]^q[o[3]]); f=m.mean()
        if f<0.01: print('CSWAP',i,o[1:4],'useful frac',f, m.sum())
        q[o[2]]^=m; q[o[3]]^=m
    elif k in ('HMR','R'): q[o[1]]=False
    elif k in ('CZ','Z'): pass
    else: print('skip',i,k)
print('done')
