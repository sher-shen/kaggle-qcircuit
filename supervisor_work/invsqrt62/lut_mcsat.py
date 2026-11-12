# exact multiplicative complexity of a multi-output 8-input boolean function via SAT (XAG, topological, affine operands)
import sys,time,numpy as np
from pysat.solvers import Cadical153
from pysat.formula import IDPool
F=np.load(sys.argv[1]); rows=[int(t) for t in sys.argv[2].split(',')]; r=int(sys.argv[3]); TL=float(sys.argv[4])
T=F[rows]; n=8; P=256
pool=IDPool(); cl=[]
def nv(): return pool.id()
TRUE=nv(); cl.append([TRUE])
def xor_eq(lits,target_lit):
    # target == XOR(lits); lits list of literals; returns clauses via chain
    if not lits: cl.append([-target_lit]); return
    acc=lits[0]
    for l in lits[1:]:
        z=nv(); # z = acc xor l
        cl.extend([[-z,acc,l],[-z,-acc,-l],[z,-acc,l],[z,acc,-l]]); acc=z
    cl.extend([[-target_lit,acc],[target_lit,-acc]])
def andv(a,b):
    z=nv(); cl.extend([[-z,a],[-z,b],[z,-a,-b]]); return z
sel={}  # (gate, operand, src) ; src 0..7 input, 8+j gate j, 'c' const
for i in range(r):
    for o in (0,1):
        for s in list(range(n+i))+['c']: sel[i,o,s]=nv()
osel={}
for k in range(len(rows)):
    for s in list(range(n+r))+['c']: osel[k,s]=nv()
# symmetry: operand 0 sources < operand 1? skip. require each gate used later (by gate or output)
for i in range(r):
    users=[sel[j,o,n+i] for j in range(i+1,r) for o in (0,1)]+[osel[k,n+i] for k in range(len(rows))]
    cl.append(users)
gv={}
for p in range(P):
    xs=[(p>>b)&1 for b in range(n)]
    vals=[]
    for i in range(r):
        ops=[]
        for o in (0,1):
            lits=[sel[i,o,s] for s in range(n) if xs[s]]+[sel[i,o,'c']]
            lits+=[andv(sel[i,o,n+j],vals[j]) for j in range(i)]
            t=nv(); xor_eq(lits,t); ops.append(t)
        g=andv(ops[0],ops[1]); vals.append(g)
    for k in range(len(rows)):
        lits=[osel[k,s] for s in range(n) if xs[s]]+[osel[k,'c']]+[andv(osel[k,n+j],vals[j]) for j in range(r)]
        t=TRUE if T[k,p] else -TRUE
        xor_eq(lits,t)
print('vars',pool.top,'clauses',len(cl),flush=True)
s=Cadical153(bootstrap_with=cl); t0=time.time()
import threading
timer=threading.Timer(TL,lambda:s.interrupt()); timer.start()
res=s.solve_limited(expect_interrupt=True); timer.cancel()
print('rows',rows,'r',r,'result',res,'time %.1f'%(time.time()-t0))
