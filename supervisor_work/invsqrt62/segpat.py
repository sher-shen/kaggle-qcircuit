"""Basis-state sim of ops.json up to op A; print distinct value patterns of given wires at A (and at B).
Usage: segpat.py ops.json A B wires(comma) [n_random]"""
import json,sys,numpy as np, collections
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits']
A=int(sys.argv[2]);Bn=int(sys.argv[3]);W=[int(w) for w in sys.argv[4].split(',')]
nr=int(sys.argv[5]) if len(sys.argv)>5 else 20000
rng=np.random.default_rng(3);MAXX=3*(2**10-2)**2
xs=np.unique(np.concatenate([np.arange(1,5000),rng.integers(1,MAXX+1,nr)]));xs=np.repeat(xs,4)
N=len(xs);q=np.zeros((nq,N),bool)
for k,qq in enumerate(d['x_qubits']): q[qq]=(xs>>k)&1
bits={};B=lambda i: bits.setdefault(i,np.zeros(N,bool));stack=[];act=np.ones(N,bool)
snap={}
for i,o in enumerate(ops):
    if i==A: snap['A']=(q[W].copy(),act.copy())
    if i==Bn: snap['B']=(q[W].copy(),act.copy()); break
    k=K[o[0]]
    if k=='PUSH_CONDITION': stack.append(act);act=act&B(o[1]);continue
    if k=='POP_CONDITION': act=stack.pop();continue
    cond=o[-2] if k=='Z_POW' else o[-1]
    m=act&B(cond) if cond>=0 else act
    a=o[1:]
    if k=='X': q[a[0]]^=m
    elif k=='CX': q[a[1]]^=m&q[a[0]]
    elif k=='CCX': q[a[2]]^=m&q[a[0]]&q[a[1]]
    elif k=='CSWAP':
        u,v=q[a[1]],q[a[2]];sw=m&q[a[0]]&(u!=v);u^=sw;v^=sw
    elif k=='SWAP':
        u,v=q[a[0]],q[a[1]];sw=m&(u!=v);u^=sw;v^=sw
    elif k in('HMR','R'):
        r=rng.random(N)<0.5
        if k=='HMR': bb=B(a[1]);bb[m]=r[m]
        q[a[0]]&=~m
    elif k=='BIT_INVERT': B(a[0])[m]^=True
    elif k=='BIT_STORE0': B(a[0])[m]=False
    elif k=='BIT_STORE1': B(a[0])[m]=True
for key in ('A','B'):
    if key not in snap: continue
    v,ac=snap[key]
    c=collections.Counter(''.join('1' if b else '0' for b in v[:,j]) for j in range(N))
    print(key,'wires',W,'active frac',ac.mean(),'distinct',len(c))
    for p,n in sorted(c.items(),key=lambda t:-t[1])[:40]: print('  ',p,n)
