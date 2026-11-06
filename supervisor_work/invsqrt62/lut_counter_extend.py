import sys,numpy as np,itertools
F=np.load(sys.argv[1]).astype(np.int64); W=[22,24]+list(range(29,62)); idx={w:i for i,w in enumerate(W)}
a=np.arange(256); A=[(a>>i)&1 for i in range(8)]
def val(cols):
    v=np.zeros(256,np.int64)
    for c in cols: v=2*v+c
    return v
def rough(v): return sum(np.abs(np.diff(v[h*128:(h+1)*128].astype(float),2)).sum() for h in (0,1))
np.random.seed(1)
for name,top in (('A',[41,57,40,51,50]),('B',[60,44,43,59,24,42])):
    cols=[F[idx[w]] for w in top]; used=set(top); desc=list(map(str,top))
    for step in range(12):
        basis=A+cols
        best=None
        for w in W:
            if w in used: continue
            for k in range(0,3):
                for sub in itertools.combinations(range(len(basis)),k):
                    c=F[idx[w]].copy()
                    for s in sub: c=c^basis[s]
                    r=rough(val(cols+[c]))
                    if best is None or r<best[0]: best=(r,w,sub,c)
        rnds=[rough(val(cols+[np.random.randint(0,2,256)])) for _ in range(20)]
        print(name,'step',step,'best',best[1],best[2],'rough',best[0],'random min',min(rnds))
        if best[0]>=min(rnds)*0.95: break
        cols.append(best[3]); used.add(best[1]); desc.append('%d^%s'%(best[1],best[2]))
    print(name,'chain',desc)
