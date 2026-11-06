import json,sys,numpy as np,collections
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits']
A,Bn=int(sys.argv[2]),int(sys.argv[3])
z=np.load('w/cl.npz');qa=z['qa']
addr=sum(qa[14+i].astype(int)<<i for i in range(8))
# pick one representative sample per address
rep=np.array([np.nonzero(addr==a)[0][0] for a in range(256)])
q=qa[:,rep].copy()  # 62x256, assume deterministic within segment except HMR
def anf(t):
    t=t.astype(np.uint8).copy()
    for i in range(8):
        s=1<<i
        for a in range(256):
            if a&s: t[a]^=t[a^s]
    return t
pc=np.array([bin(a).count('1') for a in range(256)])
def desc(v):
    a=anf(v);ms=np.nonzero(a)[0]
    return f"deg{pc[ms].max() if len(ms) else -1}/t{len(ms)}"
cnt=collections.Counter();kinds=collections.Counter()
lines=[]
for i in range(A,Bn):
    o=ops[i];k=K[o[0]];kinds[k]+=1
    if k in('PUSH_CONDITION','POP_CONDITION','Z_POW','BIT_INVERT','BIT_STORE0','BIT_STORE1'): continue
    a=o[1:]
    if k=='X': q[a[0]]^=True
    elif k=='CX': q[a[1]]^=q[a[0]]
    elif k=='CCX':
        c1,c2=q[a[0]],q[a[1]]; pa=anf(c1&c2); ms=np.nonzero(pa)[0]
        lines.append((i,a,desc(c1),desc(c2),desc(c1&c2),desc(q[a[2]])))
        q[a[2]]^=c1&c2
    elif k=='CSWAP':
        u,v=q[a[1]],q[a[2]];sw=q[a[0]]&(u!=v);u^=sw;v^=sw
    elif k=='SWAP':
        u,v=q[a[0]],q[a[1]];sw=(u!=v);u^=sw;v^=sw
    elif k in('HMR','R'): q[a[0]]=False
print(kinds)
for l in lines: print(*l)
