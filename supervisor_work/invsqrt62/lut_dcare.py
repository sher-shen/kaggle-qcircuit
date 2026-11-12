"""Per (output wire, address) slack of coeff_lookup: flip output wire w (for every x) right after the stage
and record, per address, the worst phase-error ratio and dirty count over sampled x.
usage: python dcare.py ops.json nrand seed reps out.npz [B=15214]"""
import json,sys,math,numpy as np
from multiprocessing import Pool
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits'];ZP=d['zpow_exact']
M64=(1<<64)-1;HALF=np.uint64(1<<63)
def units(i):
    n=int(ZP[str(i)]);return (((n>>63)+1)>>1)&M64
U={i:np.uint64(units(i)) for i,o in enumerate(ops) if K[o[0]]=='Z_POW'}
B0=int(sys.argv[6]) if len(sys.argv)>6 else 15214
OUTS=[22,24]+list(range(29,62))
FORCE=set()
_seen=set()
for _i in range(B0,len(ops)):
    if K[ops[_i][0]]=='HMR' and ops[_i][1] in OUTS and ops[_i][1] not in _seen: _seen.add(ops[_i][1]);FORCE.add(_i)
MAXX=3*(2**10-2)**2
rng0=np.random.default_rng(int(sys.argv[3]))
xs=np.unique(np.concatenate([np.arange(1,5000),rng0.integers(1,MAXX+1,int(sys.argv[2]))]))
xs=np.repeat(xs,int(sys.argv[4]))
def run(st,lo,hi,rng):
    q,bits,ph,tof,stack,act=st;N=q.shape[1]
    B=lambda i: bits.setdefault(i,np.zeros(N,bool))
    for i in range(lo,hi):
        o=ops[i];k=K[o[0]]
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
            if i in FORCE: r[:]=False
            ph^=np.where(m&q[a[0]]&r,HALF,np.uint64(0))
            if k=='HMR': bb=B(a[1]);bb[m]=r[m]
            q[a[0]]&=~m
        elif k=='BIT_INVERT': B(a[0])[m]^=True
        elif k=='BIT_STORE0': B(a[0])[m]=False
        elif k=='BIT_STORE1': B(a[0])[m]=True
        elif k=='Z_POW': ph+=np.where(m&q[a[0]],U[i],np.uint64(0))
    return (q,bits,ph,tof,stack,act)
X=xs.astype(np.int64);N=len(X)
q=np.zeros((nq,N),bool)
for k,qq in enumerate(d['x_qubits']): q[qq]=(X>>k)&1
st=run((q,{},np.zeros(N,np.uint64),np.zeros(N,np.int32),[],np.ones(N,bool)),0,B0,np.random.default_rng(1))
addr=sum(st[0][14+i].astype(int)<<i for i in range(8))
rs=[math.isqrt((1<<130)//int(x)) for x in X]
tgt=np.array([((r+1)>>1)&M64 for r in rs],dtype=np.uint64);tol=np.array([min(r>>25,1<<63) for r in rs],dtype=np.uint64)
anc=[i for i in range(nq) if i not in d['x_qubits']]
def score(s):
    q,bits,ph=s[0],s[1],s[2]
    err=np.abs((ph-tgt).view(np.int64)).astype(float)/tol.astype(float)
    xq=np.zeros(N,np.int64)
    for k,qq in enumerate(d['x_qubits']): xq|=q[qq].astype(np.int64)<<k
    dirty=(xq!=X)|q[anc].any(0)
    E=np.zeros(256);D=np.zeros(256,int)
    np.maximum.at(E,addr,err);np.add.at(D,addr,dirty)
    return E,D
def cp(s): return (s[0].copy(),{k:v.copy() for k,v in s[1].items()},s[2].copy(),s[3].copy(),list(s[4]),s[5].copy())
def job(w):
    s=cp(st)
    if w>=0: s[0][w]^=True
    s=run(s,B0,len(ops),np.random.default_rng(2))
    return score(s)
if __name__=='__main__':
    with Pool(4) as p: R=p.map(job,[-1]+OUTS)
    E=np.array([r[0] for r in R]);D=np.array([r[1] for r in R])
    np.savez(sys.argv[5],E=E,D=D,outs=np.array([-1]+OUTS),cnt=np.bincount(addr,minlength=256))
    print('base worst',E[0].max(),'dirty',D[0].sum())
    for j,w in enumerate(OUTS):
        ok=(E[j+1]<=1)&(D[j+1]==0)
        print(w,'ok addrs',ok.sum())
