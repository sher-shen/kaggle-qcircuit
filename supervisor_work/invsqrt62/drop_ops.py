# Delete op indices from an ops.json (re-keys zpow_exact). Usage: drop_ops.py in.json out.json i1,i2,...
import json,sys
d=json.load(open(sys.argv[1])); D=sorted(int(t) for t in sys.argv[3].split(','))
import bisect
for i in reversed(D): del d['ops'][i]
d['zpow_exact']={str(int(k)-bisect.bisect_left(D,int(k))):v for k,v in d['zpow_exact'].items() if int(k) not in D}
d['n_ops']=len(d['ops']); json.dump(d,open(sys.argv[2],'w'))
