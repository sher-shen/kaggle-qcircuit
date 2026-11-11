# For each CSWAP level in normalize: GF(2) rank of the products c*(a^b) over all x, modulo the span of live wires + 1.
# If the product rank of a level is below its CSWAP count, two CSWAPs could share one AND.
import json, sys, numpy as np
d=json.load(open(sys.argv[1])); K=d['kinds']
X=np.arange(0,3133453,dtype=np.int64); N=len(X)
q=np.zeros((64,N),dtype=bool)
for j in range(22): q[j]=(X>>j)&1
def toint(v): return int.from_bytes(np.packbits(v.astype(np.uint8)).tobytes(),'big')
def reduce(basis,v):
    for p,b in basis:
        if (v>>p)&1: v^=b
    return v
def add(basis,v):
    v=reduce(basis,v)
    if v: basis.append((v.bit_length()-1,v)); return True
    return False
levels={}
for i in range(0,238):
    o=d['ops'][i]; k=K[o[0]]
    if k=='CSWAP':
        c,a,b=o[1:4]; levels.setdefault(c,[]).append((i,q[c]&(q[a]^q[b])))
        if len(levels[c])==1: levels[c+100]=[q[w].copy() for w in range(64) if q[w].any() and not q[w].all()]
        m=q[c]&(q[a]^q[b]); q[a]^=m; q[b]^=m
    elif k=='X': q[o[1]]^=True
    elif k=='CX': q[o[2]]^=q[o[1]]
    elif k=='CCX': q[o[3]]^=q[o[1]]&q[o[2]]
    elif k in ('HMR','R'): q[o[1]]=False
for c in sorted(x for x in levels if x<100):
    base=[]; add(base,toint(np.ones(N,bool)))
    for w in levels[c+100]: add(base,toint(w))
    r=sum(add(base,toint(v)) for _,v in levels[c])
    print('level ctrl q%d: %d CSWAPs, product rank mod affine(live wires) = %d'%(c,len(levels[c]),r),flush=True)
