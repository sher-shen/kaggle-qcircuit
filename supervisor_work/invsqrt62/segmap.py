"""segmap.py ops.json A B inwires outwires bits nrand reps : truth table of segment [A,B) incl. half-turn phase"""
import json,sys,numpy as np,collections
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits']
A=int(sys.argv[2]);Bn=int(sys.argv[3])
IW=[int(w) for w in sys.argv[4].split(',')];OW=[int(w) for w in sys.argv[5].split(',')]
BI=[int(w) for w in sys.argv[6].split(',')] if sys.argv[6] else []
nr=int(sys.argv[7]);reps=int(sys.argv[8])
rng=np.random.default_rng(11);MAXX=3*(2**10-2)**2
xs=np.unique(np.concatenate([np.arange(1,5000),rng.integers(1,MAXX+1,nr)]));xs=np.repeat(xs,reps)
N=len(xs);q=np.zeros((nq,N),bool)
for k,qq in enumerate(d['x_qubits']): q[qq]=(xs>>k)&1
bits={};B=lambda i: bits.setdefault(i,np.zeros(N,bool));stack=[];act=np.ones(N,bool)
ph=np.zeros(N,bool)
for i,o in enumerate(ops):
    if i==A:
        inv=np.array([q[w] for w in IW]+[B(b).copy() for b in BI]);ph[:]=False
        live0=q.any(1)
    if i==Bn: break
    k=K[o[0]]
    if k=='PUSH_CONDITION': stack.append(act);act=act&B(o[1]);continue
    if k=='POP_CONDITION': act=stack.pop();continue
    cond=o[-2] if k=='Z_POW' else o[-1]
    m=act&B(cond) if cond>=0 else act
    a=o[1:]
    if k=='X': q[a[0]]^=m
    elif k=='CX': q[a[1]]^=m&q[a[0]]
    elif k=='CCX': q[a[2]]^=m&q[a[0]]&q[a[1]]
    elif k=='Z': ph^=m&q[a[0]]
    elif k=='CZ': ph^=m&q[a[0]]&q[a[1]]
    elif k=='CCZ': ph^=m&q[a[0]]&q[a[1]]&q[a[2]]
    elif k=='NEG': ph^=m
    elif k=='CSWAP':
        u,v=q[a[1]],q[a[2]];sw=m&q[a[0]]&(u!=v);u^=sw;v^=sw
    elif k=='SWAP':
        u,v=q[a[0]],q[a[1]];sw=m&(u!=v);u^=sw;v^=sw
    elif k in('HMR','R'):
        r=rng.random(N)<0.5
        if i>=A: ph^=m&q[a[0]]&r
        if k=='HMR': bb=B(a[1]);bb[m]=r[m]
        q[a[0]]&=~m
    elif k=='BIT_INVERT': B(a[0])[m]^=True
    elif k=='BIT_STORE0': B(a[0])[m]=False
    elif k=='BIT_STORE1': B(a[0])[m]=True
    elif k=='Z_POW':
        if i>=A: print('zpow inside',i)
outv=np.array([q[w] for w in OW])
s=lambda v:''.join('1' if b else '0' for b in v)
T=collections.defaultdict(collections.Counter)
for j in range(N): T[s(inv[:,j])][s(outv[:,j])+' ph'+('1' if ph[j] else '0')]+=1
print('in',IW,'bits',BI,'-> out',OW)
for k in sorted(T): print(k,dict(T[k]))
print('live at A (non-zero somewhere):',[w for w in range(nq) if live0[w]])
