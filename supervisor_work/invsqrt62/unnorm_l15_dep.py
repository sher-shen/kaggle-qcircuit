# Which CSWAP products of unnormalize level q15 (ops 46791..46806) are affine-dependent on the others + live wires?
import json, sys, numpy as np
from simto import sim
d=json.load(open(sys.argv[1])); K=d['kinds']; ops=d['ops']
N=int(sys.argv[2]); rng=np.random.default_rng(int(sys.argv[3]))
xs=np.sort(rng.choice(3133453,N,replace=False)).astype(np.int64) if N<3133453 else np.arange(3133453,dtype=np.int64)
q,bits=sim(d,xs,46791,1)
pre=q.copy(); prods=[]
for i in range(46791,46807):
    o=ops[i]; k=K[o[0]]; a=o[1:]
    if k=='CSWAP': m=q[a[0]]&(q[a[1]]^q[a[2]]); prods.append((i,a[:3],m.copy(),q[a[1]].copy(),q[a[2]].copy())); q[a[1]]^=m; q[a[2]]^=m
    elif k=='CX': q[a[1]]^=q[a[0]]
    elif k=='X': q[a[0]]^=True
for i,a,m,u,v in prods: print(i,a,'fires',m.mean(),'u const',(u.all() or not u.any()),'v const',(v.all() or not v.any()), 'u==v frac',(u==v).mean())
# Gaussian elimination tracking: base = 1 + live wires; then products in order; print which are dependent
def toint(v): return int.from_bytes(np.packbits(v.astype(np.uint8)).tobytes(),'big')
base=[]
def add(v):
    for p,b in base:
        if (v>>p)&1: v^=b
    if v: base.append((v.bit_length()-1,v)); return True
    return False
add(toint(np.ones(N,bool)))
for w in range(pre.shape[0]):
    if pre[w].any() and not pre[w].all(): add(toint(pre[w]))
print('live dim',len(base))
for i,a,m,u,v in prods: print(i,'independent' if add(toint(m)) else 'DEPENDENT')
