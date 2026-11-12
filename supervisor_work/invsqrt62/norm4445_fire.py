import json, sys, numpy as np
d=json.load(open(sys.argv[1])); K=d['kinds']
sn=np.load(sys.argv[2]); raw=sn[0]
u=raw[44]^raw[43]; v=raw[45]^raw[44]
cases={'10':u&~v,'01':~u&v,'11':u&v}
q=sn[3].copy()
for i in range(186,218):
    o=d['ops'][i]; k=K[o[0]]
    if k=='CSWAP':
        c,a,b=o[1],o[2],o[3]; m=q[c]&(q[a]^q[b])
        print(i,'CSWAP',c,a,b,' '.join('%s:%d'%(n,(m&cm).sum()) for n,cm in cases.items()))
        q[a]^=m; q[b]^=m
    elif k=='X': q[o[1]]^=True
    elif k=='CX': q[o[2]]^=q[o[1]]
    elif k=='CCX': q[o[3]]^=q[o[1]]&q[o[2]]
    elif k in ('HMR','R'): print(i,k,o[1:]); q[o[1]]=False
    else: print(i,k,o[1:])
