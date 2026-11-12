import numpy as np, sys
sn=np.load(sys.argv[1]); raw=sn[0]; pre=sn[3]; post=sn[5]
for k in range(8):
    m=(raw[43]==(k&1))&(raw[44]==((k>>1)&1))&(raw[45]==((k>>2)&1)); n=m.sum()
    if n==0: continue
    out=[]
    for w in range(23):
        P=post[w,m]
        if not P.any(): out.append('%d=0'%w); continue
        if P.all(): out.append('%d=1'%w); continue
        src=[s for s in range(23) if (pre[s,m]==P).all()]
        srcn=[s for s in range(23) if (pre[s,m]==~P).all()]
        out.append('%d<-%s'%(w,(src or ['~%s'%srcn if srcn else '?'])[0] if src or srcn else '?'))
    print(k&1,(k>>1)&1,k>>2,' '.join(out))
    print('   pre zero:',[w for w in range(23) if not pre[w,m].any()],'one:',[w for w in range(23) if pre[w,m].all()])
