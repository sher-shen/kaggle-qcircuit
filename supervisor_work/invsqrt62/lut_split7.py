import json,sys
d=json.load(open(sys.argv[1]))
N=256;FULL=(1<<N)-1
x=[sum(1<<a for a in range(N) if a>>i&1) for i in range(8)]
A=[]
def lin(m,c):
    v=FULL if c else 0
    for i in range(8):
        if m>>i&1: v^=x[i]
    j=0;m>>=8
    while m:
        if m&1: v^=A[j]
        m>>=1;j+=1
    return v
for ma,ca,mb,cb in d['ands']:
    A.append(lin(int(ma,16),ca)&lin(int(mb,16),cb))
F=[lin(int(m,16),c) for m,c in d['outs']]
def anf(tt,n):
    t=[(tt>>a)&1 for a in range(1<<n)]
    for i in range(n):
        for a in range(1<<n):
            if a>>i&1: t[a]^=t[a^(1<<i)]
    return t
def rank(vs):
    vs=list(vs);r=0;basis=[]
    for v in vs:
        for b in basis: v=min(v,v^b)
        if v: basis.append(v);r+=1
    return r
used=set()
for f in F:
    a=anf(f,8);used|={m for m in range(256) if a[m] and bin(m).count('1')>=2}
print('8-var monomials deg>=2 used by any output:',len(used),'of 247')
H=(1<<128)-1
g=[f&H for f in F]; f1=[f>>128 for f in F]; h=[a^b for a,b in zip(g,f1)]
print('rank g',rank(g),'rank h',rank(h),'rank f',rank(F))
ug=set();uh=set()
for gg,hh in zip(g,h):
    a=anf(gg,7);ug|={m for m in range(128) if a[m] and bin(m).count('1')>=2}
    a=anf(hh,7);uh|={m for m in range(128) if a[m] and bin(m).count('1')>=1}
print('g monomials',len(ug),'h monomials (deg>=1)',len(uh))
print('split cost (35 h-scratch): 120 +',rank(h),'=',120+rank(h),' ; in-place DFS (<=7 scratch):',len(ug)+len(uh), '; public 177')
import numpy as np
np.save(sys.argv[2],np.array([[f>>a&1 for a in range(256)] for f in F],dtype=np.uint8))
