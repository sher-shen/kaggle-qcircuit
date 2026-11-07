"""stage_match.py A62 A63 ops62.json ops63.json: match live wires of two builds at stage starts (equal / GF(2)-affine)."""
import sys,json,numpy as np
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from simto import sim
d62=json.load(open(sys.argv[3]));d63=json.load(open(sys.argv[4]))
rng=np.random.default_rng(5);MAXX=3*(2**10-2)**2
xs=np.unique(np.concatenate([np.arange(1,3000),rng.integers(1,MAXX+1,6000)])).astype(np.int64)
A62,A63=int(sys.argv[1]),int(sys.argv[2])
res={}
for nm,d,A in [('62',d62,A62),('63',d63,A63)]:
    qa,_=sim(d,xs,A,1);qb,_=sim(d,xs,A,2)
    live=[w for w in range(d.get('n_qubits',63)) if qa[w].any() or qb[w].any()]
    hist=[w for w in live if (qa[w]!=qb[w]).any()]
    res[nm]=(qa,live,hist);print(nm,'live',len(live),live,'history-dependent',hist)
qa62,l62,_=res['62'];qa63,l63,_=res['63']
mp={}
for w in l63:
    c=[v for v in l62 if (qa62[v]==qa63[w]).all()]
    mp[w]=c
print('map63->62',mp)
import itertools
basis=[np.ones(len(xs),bool)]+[qa62[v] for v in l62];names=['1']+[str(v) for v in l62]
def solve(t):
    # gaussian elimination over GF2, columns = samples
    M=np.array(basis+[t],dtype=np.uint8).T  # samples x (n+1)
    n=len(basis);A=M[:,:n].copy();b=M[:,n].copy();piv=[];r=0
    for c in range(n):
        rows=np.nonzero(A[r:,c])[0]
        if len(rows)==0: continue
        p=rows[0]+r;A[[r,p]]=A[[p,r]];b[[r,p]]=b[[p,r]]
        sel=np.nonzero(A[:,c])[0];sel=sel[sel!=r];A[sel]^=A[r];b[sel]^=b[r];piv.append(c);r+=1
        if r==A.shape[0]: break
    if b[r:].any(): return None
    return [names[c] for i,c in enumerate(piv) if b[i]]
for w in [0,2,3,23,56]:
    print('63q wire',w,'= XOR of 62q',solve(qa63[w]))
for w in [0,2,3,23]:
    basis2=[np.ones(len(xs),bool)]+[qa63[v] for v in l63]
print('62q wires 0,2,3,23 stats',[qa62[w].mean() for w in [0,2,3,23]],'63q 0,2,3,23,56',[qa63[w].mean() for w in [0,2,3,23,56]])
