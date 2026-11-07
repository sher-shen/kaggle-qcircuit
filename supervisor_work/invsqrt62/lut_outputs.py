import numpy as np,sys
z=np.load(sys.argv[1]);qa,qb,ph=z['qa'],z['qb'],z['ph']
nq=qa.shape[0]
addr=sum(qa[14+i].astype(int)<<i for i in range(8))
print('addr coverage',len(np.unique(addr)))
live_a=[w for w in range(nq) if qa[w].any()]; live_b=[w for w in range(nq) if qb[w].any()]
print('live A',live_a);print('live B',live_b)
# which output wires are functions of (addr, prior wire)?
out=[]
for w in live_b:
    # check if qb[w]^qa[w] is a function of addr
    v=qb[w]^qa[w]
    f=np.full(256,-1)
    ok=True
    for ad in range(256):
        s=v[addr==ad]
        if len(s)==0: continue
        if s.all(): f[ad]=1
        elif (~s).all(): f[ad]=0
        else: ok=False;break
    print(w,'func' if ok else 'NOT', ''.join(map(str,f)) if ok and w not in range(14,22) else '')
    if ok and v.any(): out.append((w,f))
print('phase func of addr?', all(len(set(ph[addr==a]))<=1 for a in range(256)))
np.save(sys.argv[2],np.array([f for w,f in out]))
print('outputs',[w for w,f in out])
