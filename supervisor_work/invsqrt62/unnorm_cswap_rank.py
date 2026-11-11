# unnormalize CSWAP ladder (ops ~46791..46863): per-level product rank and cross-level lower bound, on a random sample of x.
# A bound computed on a subset of inputs is still a valid lower bound on ANDs (rank can only grow with more inputs).
# Usage: python3.13 unnorm_cswap_rank.py ops.json NSAMPLE SEED
import json, sys, numpy as np
from simto import sim
d=json.load(open(sys.argv[1])); K=d['kinds']; ops=d['ops']
N=int(sys.argv[2]); rng=np.random.default_rng(int(sys.argv[3]))
xs=np.sort(rng.choice(3133453,N,replace=False)).astype(np.int64)
A0,B0=46788,46865
q,bits=sim(d,xs,A0,1)
def toint(v): return int.from_bytes(np.packbits(v.astype(np.uint8)).tobytes(),'big')
def add(basis,v):
    for p,b in basis:
        if (v>>p)&1: v^=b
    if v: basis.append((v.bit_length()-1,v)); return True
    return False
snap={}; cnt={}; prods={}; live={}; order=[]; prev=None
for i in range(A0,B0):
    o=ops[i]; k=K[o[0]]; a=o[1:]
    if k=='CSWAP':
        c=a[0]; key=(len(order),c)
        if prev is None or prev[1]!=c:
            if prev is not None: snap[('post',prev)]=q.copy()
            snap[('pre',key)]=q.copy(); order.append(key); cnt[key]=0; prods[key]=[]; prev=key
        cnt[prev]+=1; m=q[c]&(q[a[1]]^q[a[2]]); prods[prev].append(m.copy()); q[a[1]]^=m; q[a[2]]^=m
    elif k=='X': q[a[0]]^=True
    elif k=='CX': q[a[1]]^=q[a[0]]
    elif k=='CCX': q[a[2]]^=q[a[0]]&q[a[1]]
    elif k=='SWAP': t=q[a[0]].copy(); q[a[0]]=q[a[1]]; q[a[1]]=t
    elif k in('HMR','R'): q[a[0]]=False
    elif k in('CZ','Z'): pass
    else: print('skip',i,k)
snap[('post',prev)]=q.copy()
def affbase(S):
    base=[]; add(base,toint(np.ones(N,bool)))
    for w in range(S.shape[0]):
        if S[w].any() and not S[w].all(): add(base,toint(S[w]))
    return base
print('levels',order,'counts',[cnt[c] for c in order],'N',N)
for key in order:
    base=affbase(snap[('pre',key)]); r=sum(add(base,toint(v)) for v in prods[key])
    print('level',key,'CSWAPs',cnt[key],'product rank mod affine(live)',r,flush=True)
for L in range(len(order)):
    for R in range(L+1,len(order)):
        g=order[L:R+1]; base=affbase(snap[('pre',g[0])]); B=snap[('post',g[-1])]
        r=sum(add(base,toint(B[w])) for w in range(B.shape[0]) if B[w].any() and not B[w].all())
        print('group',g,'CSWAPs',sum(cnt[c] for c in g),'lower bound',r,flush=True)
