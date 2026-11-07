"""Per-rotation Toffoli counts of one stage, 62q public circuit vs 63q 9a8627.  Usage: python segtof.py <circuit-viewer dir> <stage>"""
import json,sys
V=sys.argv[1]; st=sys.argv[2]
def seg(opsf,stf):
    a=json.load(open(opsf));K=a['kinds']
    s={s['id']:s for s in json.load(open(stf))['stages']}[st]
    res=[];t=0;cond=0;st0=s['start']
    for i in range(s['start'],s['end']):
        o=a['ops'][i];k=K[o[0]]
        if k in('CCX','CCZ','CSWAP'): t+=1
        if k=='Z_POW': res.append((st0,i,t,o[-1]));t=0;st0=i+1
    res.append((st0,s['end'],t,None));return res
A=seg(V+'/ops.json',V+'/stages.json');B=seg(V+'/circuits/9a8627/ops.json',V+'/circuits/9a8627/stages.json')
for x,y in zip(A,B): print(x,'|',y, '<<' if x[2]!=y[2] else '')
