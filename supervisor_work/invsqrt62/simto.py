import json,numpy as np
def sim(d,xs,stop,seed):
    K=d['kinds'];ops=d['ops'];nq=d.get('n_qubits',63);rng=np.random.default_rng(seed);N=len(xs)
    q=np.zeros((nq,N),bool)
    for k,qq in enumerate(d['x_qubits']): q[qq]=(xs>>k)&1
    bits={};B=lambda i: bits.setdefault(i,np.zeros(N,bool));stack=[];act=np.ones(N,bool);ph=np.zeros(N,bool)
    for i,o in enumerate(ops[:stop]):
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
    return q,bits
