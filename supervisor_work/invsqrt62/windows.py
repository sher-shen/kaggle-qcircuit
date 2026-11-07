import json, sys, numpy as np
s=json.load(open(sys.argv[1]))['stages']; o=np.load(sys.argv[2])
m=(o==62).astype(int); d=np.diff(np.r_[0,m,0]); st=np.nonzero(d==1)[0]; en=np.nonzero(d==-1)[0]
# merge windows separated by <=3 ops
W=[]
for a,b in zip(st,en):
    if W and a-W[-1][1]<=3: W[-1][1]=b
    else: W.append([a,b])
from collections import defaultdict
agg=defaultdict(lambda:[0,0])
for a,b in W:
    sid=[t['id'] for t in s if t['start']<=a<t['end']][0]; agg[sid][0]+=1; agg[sid][1]+=b-a
for k,v in agg.items(): print(k,'windows',v[0],'ops',v[1])
np.save(sys.argv[3], np.array(W))
