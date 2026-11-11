import numpy as np, sys
sn=np.load(sys.argv[1]); raw=sn[0]; pre=sn[3]; post=sn[5]
def toint(v): return int.from_bytes(np.packbits(v.astype(np.uint8)).tobytes(),'big')
def rank(vecs):
    basis=[]
    for x in vecs:
        x=toint(x)
        for p,b in basis:
            if (x>>p)&1: x^=b
        if x: basis.append((x.bit_length()-1,x))
    return len(basis)
W=list(range(23))
for k in range(8):
    m=(raw[43]==(k&1))&(raw[44]==((k>>1)&1))&(raw[45]==((k>>2)&1)); n=m.sum()
    if n==0: continue
    dl=[pre[w,m]^post[w,m] for w in W]
    pv=[pre[w,m] for w in range(64) if pre[w,m].any() and not pre[w,m].all()]
    print('r43,r44,r45=',k&1,(k>>1)&1,k>>2,'|D|',n,'rankDelta',rank(dl),'w/1',rank(dl+[np.ones(n,bool)]),'dim pre',rank(pv+[np.ones(n,bool)]), 'chg', [w for w in W if dl[w].any()])
