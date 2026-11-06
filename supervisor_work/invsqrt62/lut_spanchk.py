import json,sys,numpy as np
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits']
A,Bn=int(sys.argv[2]),int(sys.argv[3])
z=np.load('w/cl.npz');qa=z['qa']
addr=sum(qa[14+i].astype(int)<<i for i in range(8))
rep=np.array([np.nonzero(addr==a)[0][0] for a in range(256)])
q=qa[:,rep].copy()
def pack(v): return int(''.join('1' if b else '0' for b in v),2)
def inspan(vecs,t):
    # gaussian elimination over python ints
    basis={}
    for v in vecs:
        while v:
            h=v.bit_length()-1
            if h in basis: v^=basis[h]
            else: basis[h]=v;break
    while t:
        h=t.bit_length()-1
        if h in basis: t^=basis[h]
        else: return False
    return True
ONE=(1<<256)-1
hits=0;n=0
for i in range(A,Bn):
    o=ops[i];k=K[o[0]]
    if k in('PUSH_CONDITION','POP_CONDITION','Z_POW','BIT_INVERT','BIT_STORE0','BIT_STORE1'): continue
    a=o[1:]
    if k=='X': q[a[0]]^=True
    elif k=='CX': q[a[1]]^=q[a[0]]
    elif k=='CCX':
        n+=1
        p=q[a[0]]&q[a[1]]
        live=[pack(q[w]) for w in range(nq) if q[w].any()]+[ONE]
        if inspan(live,pack(p)): hits+=1;print('HIT',i,a)
        q[a[2]]^=p
    elif k=='CSWAP':
        u,v=q[a[1]],q[a[2]];sw=q[a[0]]&(u!=v);u^=sw;v^=sw
    elif k=='SWAP':
        u,v=q[a[1]] if False else q[a[0]],q[a[1]];sw=(u!=v);u^=sw;v^=sw
    elif k in('HMR','R'): q[a[0]]=False
print('ccx',n,'hits',hits)
