# Full-domain check: does CSWAP 46791 / 46792 ever swap differing values? (chunks of x; HMR outcomes random, several seeds)
import json, sys, numpy as np
from simto import sim
d=json.load(open(sys.argv[1])); ops=d['ops']; seed=int(sys.argv[2]); CH=int(sys.argv[3]) if len(sys.argv)>3 else 400000
tot={46791:0,46792:0}; c15=0
for s in range(0,3133453,CH):
    xs=np.arange(s,min(s+CH,3133453),dtype=np.int64)
    q,_=sim(d,xs,46791,seed+s)
    m1=q[15]&(q[61]^q[28]); tot[46791]+=int(m1.sum()); u,v=q[61]^m1,q[28]^m1; q[61],q[28]=u,v
    m2=q[15]&(q[27]^q[40]); tot[46792]+=int(m2.sum()); c15+=int(q[15].sum())
    print(s,tot,'q15=1:',c15,flush=True)
print('FINAL',tot,'q15=1 count',c15)
