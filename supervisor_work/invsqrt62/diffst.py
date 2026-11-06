"""Op-level diff of one stage, 62q vs 63q 9a8627 (labels differ, so use with segtof.py).  Usage: python diffst.py <viewer dir> <stage>"""
import json,difflib,sys
V=sys.argv[1]; st=sys.argv[2]
a=json.load(open(V+'/ops.json')); b=json.load(open(V+'/circuits/9a8627/ops.json'))
K=a['kinds']
sa={s['id']:s for s in json.load(open(V+'/stages.json'))['stages']}[st]
sb={s['id']:s for s in json.load(open(V+'/circuits/9a8627/stages.json'))['stages']}[st]
A=[tuple(o) for o in a['ops'][sa['start']:sa['end']]]
B=[tuple(o) for o in b['ops'][sb['start']:sb['end']]]
fa=lambda o:K[o[0]]+' '+' '.join(map(str,o[1:]))
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': print('== %d ops'%(i2-i1)); continue
    print('---',tag,'62@%d'%(sa['start']+i1),'63@%d'%(sb['start']+j1))
    for o in A[i1:i2]: print('  62:',fa(o))
    for o in B[j1:j2]: print('  63:',fa(o))
