"""Fast sampled (or full) basis-state check of an ops.json invsqrt circuit: phase error vs tolerance, final
ancilla/x-register cleanliness, mean executed Toffolis.  Usage: python qcheck.py ops.json <n_random|all> [seed] [repeats_per_x]
"""
import json,sys,math,numpy as np
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits'];ZP=d['zpow_exact']
M64=(1<<64)-1;HALF=np.uint64(1<<63)
def units(i):
    n=int(ZP[str(i)]);return (((n>>63)+1)>>1)&M64
U={i:np.uint64(units(i)) for i,o in enumerate(ops) if K[o[0]]=='Z_POW'}
rng=np.random.default_rng(int(sys.argv[3]) if len(sys.argv)>3 else 7)
MAXX=3*(2**10-2)**2
mode=sys.argv[2]
if mode=='all': xs=np.arange(1,MAXX+1)
else: xs=np.unique(np.concatenate([np.arange(1,5000),rng.integers(1,MAXX+1,int(mode))]))
xs=np.repeat(xs, int(sys.argv[4]) if len(sys.argv)>4 else 1)
worst=0;bad=0;tofs=0;cnt=0;dirty=0
CH=1<<17
for s in range(0,len(xs),CH):
    X=xs[s:s+CH].astype(np.int64);N=len(X)
    q=np.zeros((nq,N),bool)
    for k,qq in enumerate(d['x_qubits']): q[qq]=(X>>k)&1
    bits={};B=lambda i: bits.setdefault(i,np.zeros(N,bool))
    ph=np.zeros(N,np.uint64);tof=np.zeros(N,np.int32);stack=[];act=np.ones(N,bool)
    for i,o in enumerate(ops):
        k=K[o[0]]
        if k=='PUSH_CONDITION': stack.append(act);act=act&B(o[1]);continue
        if k=='POP_CONDITION': act=stack.pop();continue
        cond=o[-2] if k=='Z_POW' else o[-1]
        m=act&B(cond) if cond>=0 else act
        a=o[1:]
        if k=='X': q[a[0]]^=m
        elif k=='CX': q[a[1]]^=m&q[a[0]]
        elif k=='CCX': q[a[2]]^=m&q[a[0]]&q[a[1]];tof+=m
        elif k=='Z': ph^=np.where(m&q[a[0]],HALF,np.uint64(0))
        elif k=='CZ': ph^=np.where(m&q[a[0]]&q[a[1]],HALF,np.uint64(0))
        elif k=='CCZ': ph^=np.where(m&q[a[0]]&q[a[1]]&q[a[2]],HALF,np.uint64(0));tof+=m
        elif k=='NEG': ph^=np.where(m,HALF,np.uint64(0))
        elif k=='CSWAP':
            u,v=q[a[1]],q[a[2]];sw=m&q[a[0]]&(u!=v);u^=sw;v^=sw;tof+=m
        elif k=='SWAP':
            u,v=q[a[0]],q[a[1]];sw=m&(u!=v);u^=sw;v^=sw
        elif k in('HMR','R'):
            r=rng.random(N)<0.5
            ph^=np.where(m&q[a[0]]&r,HALF,np.uint64(0))
            if k=='HMR': bb=B(a[1]);bb[m]=r[m]
            q[a[0]]&=~m
        elif k=='BIT_INVERT': B(a[0])[m]^=True
        elif k=='BIT_STORE0': B(a[0])[m]=False
        elif k=='BIT_STORE1': B(a[0])[m]=True
        elif k=='Z_POW': ph+=np.where(m&q[a[0]],U[i],np.uint64(0))
    rs=[math.isqrt((1<<130)//int(x)) for x in X]
    tgt=np.array([((r+1)>>1)&M64 for r in rs],dtype=np.uint64);tol=np.array([min(r>>25,1<<63) for r in rs],dtype=np.uint64)
    err=np.abs((ph-tgt).view(np.int64)).astype(float)/tol.astype(float)
    worst=max(worst,err.max());bad+=(err>1).sum()
    xq=np.zeros(N,np.int64)
    for k,qq in enumerate(d['x_qubits']): xq|=q[qq].astype(np.int64)<<k
    anc=[i for i in range(nq) if i not in d['x_qubits']]
    dirty+=((xq!=X)|q[anc].any(0)).sum()
    tofs+=tof.sum();cnt+=N
print('n',cnt,'worst',worst,'bad',bad,'dirty',dirty,'mean tof',tofs/cnt)
