import sys,re,collections
live=set(f'q{i}' for i in range(22)); stack=[]; peak=collections.defaultdict(int); tof=collections.Counter()
top=lambda: stack[0] if stack else '-'
for ln in open(sys.argv[1]):
    p=ln.split()
    if not p: continue
    op=p[0]
    if op=='INFO_TAG':
        t=ln.split('"')[1]
        if t.startswith('@enter:'): stack.append(t[7:])
        elif t.startswith('@exit:'): stack.pop()
        continue
    qs=[a for a in p[1:] if re.fullmatch(r'q\d+',a)]
    if op=='R': live.update(qs)
    elif op=='HMR': 
        for q in qs: live.discard(q)
    else: live.update(qs)
    if op in('CCX','CSWAP') or (op=='CZ' and False): tof[top()]+=1
    peak[top()]=max(peak[top()],len(live))
for k in peak: print(f'{k:20s} peak {peak[k]:4d}  ccx/cswap {tof[k]}')
