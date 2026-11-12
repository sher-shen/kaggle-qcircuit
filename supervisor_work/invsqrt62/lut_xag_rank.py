# XAG-level redundancy: is any AND product (truth table over 256 addresses) in the GF(2) span of
# 1, inputs and EARLIER AND products? Also: are the AND inputs' (a,b) pairs duplicated up to affine equivalence?
import re,sys,numpy as np
L=open(sys.argv[1]).read().split('\n')
tt={};A=np.arange(256)
for i in range(8): tt[f'x{i}']=((A>>i)&1).astype(np.uint8)
tt["1'b0"]=np.zeros(256,np.uint8)
def v(s):
    s=s.strip();n=s.startswith('~');s=s.lstrip('~')
    return tt[s]^n
prods=[]
for l in L:
    m=re.match(r'assign (\w+) = (.+);',l)
    if not m: continue
    lhs,rhs=m.groups()
    if '&' in rhs: a,b=rhs.split('&');tt[lhs]=v(a)&v(b);prods.append(lhs)
    elif '^' in rhs: a,b=rhs.split('^');tt[lhs]=v(a)^v(b)
    else: tt[lhs]=v(rhs)
def toint(t): return int(''.join(map(str,t[::-1])),2)
basis={}
def add(x):
    while x:
        h=x.bit_length()-1
        if h in basis: x^=basis[h]
        else: basis[h]=x;return True
    return False
add(toint(np.ones(256,np.uint8)))
for i in range(8): add(toint(tt[f'x{i}']))
red=[p for p in prods if not add(toint(tt[p]))]
print('ANDs',len(prods),'redundant (in span of earlier)',len(red),red[:10])
outs=[toint(tt[f'y{j}']) for j in range(35)]
