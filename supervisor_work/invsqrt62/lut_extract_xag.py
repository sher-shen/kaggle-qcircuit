# Extract coeff_lookup (ops A..B of ops.json) as an XAG over address q14..q21; writes verilog.
import json,sys
d=json.load(open(sys.argv[1]));K=d['kinds'];ops=d['ops'];nq=d['n_qubits']
A,B=int(sys.argv[2]),int(sys.argv[3]);out=sys.argv[4]
# node: ('in',i) | ('xor',a,b) | ('and',a,b) | const 0 ; signal = (node,compl)
nodes=[('c0',)] ; ZERO=(0,0)
def new(n): nodes.append(n); return (len(nodes)-1,0)
W={w:ZERO for w in range(nq)}
for i in range(8): W[14+i]=new(('in',i))
ext=set(list(range(14))+[23])
for w in ext: W[w]=new(('ext',w))
def xor(a,b):
    if a[0]==0: return (b[0],b[1]^a[1])
    if b[0]==0: return (a[0],a[1]^b[1])
    if a[0]==b[0]: return (0,a[1]^b[1])
    return new(('xor',a,b))
def AND(a,b): return new(('and',a,b))
ccz=[];touched=set();nand=0
for i in range(A,B):
    o=ops[i];k=K[o[0]];a=o[1:]
    if k in('PUSH_CONDITION','POP_CONDITION','Z_POW','BIT_INVERT','BIT_STORE0','BIT_STORE1','Z','CZ','NEG','S','T'): 
        if k=='PUSH_CONDITION': print('COND at',i,file=sys.stderr)
        continue
    if k=='X': W[a[0]]=(W[a[0]][0],W[a[0]][1]^1)
    elif k=='CX': W[a[1]]=xor(W[a[1]],W[a[0]])
    elif k=='CCX': W[a[2]]=xor(W[a[2]],AND(W[a[0]],W[a[1]]));nand+=1;touched|={a[0],a[1]}&ext and {a[0]} or set()
    elif k=='SWAP': W[a[0]],W[a[1]]=W[a[1]],W[a[0]]
    elif k in('HMR','R'): W[a[0]]=ZERO
    else: print('UNHANDLED',k,i,file=sys.stderr)
outs=[22,24]+list(range(29,62))
print('ands',nand,'ext touched as ctrl',touched,file=sys.stderr)
for w in ext: assert W[w]==(nodes.index(('ext',w)),0), ('ext changed',w)
# check outputs depend only on inputs (no ext)
memo={}
def dep(s):
    n=s[0]
    if n in memo: return memo[n]
    t=nodes[n]
    r = set() if t[0]=='c0' else {t} if t[0] in('in','ext') else dep(t[1])|dep(t[2])
    memo[n]=r;return r
for w in outs: assert all(x[0]=='in' for x in dep(W[w])),w
# emit verilog (only cone of outputs)
used=set();st=[W[w][0] for w in outs]
while st:
    n=st.pop()
    if n in used: continue
    used.add(n);t=nodes[n]
    if t[0] in('xor','and'): st+= [t[1][0],t[2][0]]
def nm(s):
    n,c=s;t=nodes[n]
    base='1\'b0' if t[0]=='c0' else f'x{t[1]}' if t[0]=='in' else f'n{n}'
    return ('~' if c else '')+base
L=['module top('+','.join([f'x{i}' for i in range(8)]+[f'y{j}' for j in range(len(outs))])+');']
L+=[f'input x{i};' for i in range(8)]+[f'output y{j};' for j in range(len(outs))]
for n in sorted(used):
    t=nodes[n]
    if t[0] in('xor','and'): L.append(f'wire n{n};')
na=0
for n in sorted(used):
    t=nodes[n]
    if t[0]=='xor': L.append(f'assign n{n} = {nm(t[1])} ^ {nm(t[2])};')
    if t[0]=='and': L.append(f'assign n{n} = {nm(t[1])} & {nm(t[2])};');na+=1
for j,w in enumerate(outs): L.append(f'assign y{j} = {nm(W[w])};')
L.append('endmodule');open(out,'w').write('\n'.join(L)+'\n')
print('cone ANDs',na,file=sys.stderr)
