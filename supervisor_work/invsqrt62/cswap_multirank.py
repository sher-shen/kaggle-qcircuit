# Cross-level lower bound for normalize's shift levels: for a group of consecutive CSWAP levels, any circuit mapping the
# wire state before the group to the wire state after it needs >= rank(output wires mod affine span of input wires) ANDs.
# Also checks the "sum of product ranks" upper picture: if the bound equals the CSWAP count, merging levels cannot save an AND.
import json, sys, numpy as np
d=json.load(open(sys.argv[1])); K=d['kinds']
X=np.arange(0,3133453,dtype=np.int64); N=len(X)
q=np.zeros((64,N),dtype=bool)
for j in range(22): q[j]=(X>>j)&1
def toint(v): return int.from_bytes(np.packbits(v.astype(np.uint8)).tobytes(),'big')
def add(basis,v):
    for p,b in basis:
        if (v>>p)&1: v^=b
    if v: basis.append((v.bit_length()-1,v)); return True
    return False
snap={}; cnt={}; prev=None; order=[]
for i in range(0,238):
    o=d['ops'][i]; k=K[o[0]]
    if k=='CSWAP':
        c=o[1]
        if c!=prev:
            snap[('pre',c)]=q.copy(); order.append(c); cnt[c]=0
            if prev is not None: snap[('post',prev)]=q.copy()
            prev=c
        cnt[c]+=1
        a,b=o[2],o[3]; m=q[c]&(q[a]^q[b]); q[a]^=m; q[b]^=m
    else:
        if prev is not None and ('post',prev) not in snap and k in('CCX',): pass
        if k=='X': q[o[1]]^=True
        elif k=='CX': q[o[2]]^=q[o[1]]
        elif k=='CCX': q[o[3]]^=q[o[1]]&q[o[2]]
        elif k in ('HMR','R'): q[o[1]]=False
snap[('post',prev)]=q.copy()
def bound(levs):
    A=snap[('pre',levs[0])]; B=snap[('post',levs[-1])]
    base=[]; add(base,toint(np.ones(N,bool)))
    for w in range(64):
        if A[w].any() and not A[w].all(): add(base,toint(A[w]))
    r=sum(add(base,toint(B[w])) for w in range(64) if B[w].any() and not B[w].all())
    return r
print('levels',order,'counts',[cnt[c] for c in order])
for L in range(len(order)):
    for R in range(L+1,len(order)):
        g=order[L:R+1]; print('group',g,'CSWAPs',sum(cnt[c] for c in g),'lower bound',bound(g),flush=True)
