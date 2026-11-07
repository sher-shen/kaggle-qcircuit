import os, sys, types, itertools, copy
H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,H)
sys.argv=[sys.argv[0]]+['--maxanc','13']
src=open(H+'/lutpoly17.py').read().split('sys.argv[0] =')[0]
exec(compile(src,H+'/lutpoly17.py','exec'),{'__file__':H+'/lutpoly17.py','__name__':'lp17'})
import lutpoly15 as P15, lutpoly16 as L16, lutpoly14 as P
D=L16.SDesign
D.round=(1,2)
d=D(9,2,28,guards=[0,-2,-4],rangeq=True,packflags=True)
for a in 'clamp binnorm zshift droptop smallfirst foldadd gadd'.split(): setattr(d,a,True)
d.pad=0; d.maxq=0; d.droprot=0
e=d.calibrate(); print('L',d.choose_L(), flush=True)
res=[]
for spec in sys.argv_specs if False else eval(os.environ['SPECS']):
    mx, groups = spec
    P15.mx=mx
    ok=True
    for j,(ga,gl) in groups.items():
        r=P.group_ok(d,j,ga,gl)
        if not r[0]: ok=False
    if not ok: print(spec,'group FAIL',flush=True); continue
    d.groups=groups
    if hasattr(d,'_cA'): del d._cA
    c=d.build(); Q=c.num_qubits; T=c.operation_statistics().num_toffoli_like
    print(spec,Q,T,'est',round(Q*(T+254.61)),flush=True)
