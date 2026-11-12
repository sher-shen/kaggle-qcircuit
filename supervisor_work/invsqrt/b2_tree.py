import os, sys
H=__import__('os').path.dirname(__import__('os').path.abspath(__file__)); sys.path.insert(0,H)
sys.argv=[sys.argv[0],'--maxanc','13']
import lutpoly15 as P15, lutpoly16 as L16, lutpoly14 as P, numpy as np, pickle
D=L16.SDesign; D.round=(1,2)
d=D(9,2,28,guards=[0,-2,-4],rangeq=True,packflags=True)
for a in 'clamp binnorm zshift droptop smallfirst foldadd gadd'.split(): setattr(d,a,True)
d.pad=0; d.maxq=0; d.droprot=0
d.calibrate(); d.choose_L()
c=d.coefs
print('widths',d.widths, 'D',d.D)
b2=np.array(c[2][128:]); b1=np.array(c[1][128:])
print('b2',b2[:16], b2[-16:]); print('b1',b1[:4])
for r in (1,2,3):
    g=b2.reshape(-1,2**r); print(r,'max spread in group',(g.max(1)-g.min(1)).max())
full=np.array(c[2]); 
def leaves(v,lo,hi):
    # count leaves of pruned tree on [lo,hi) ; unreachable addresses <128 are don't-care
    seg=[a for a in range(lo,hi) if a>=128]
    if not seg: return 0
    if len(set(v[a] for a in seg))==1: return 1
    m=(lo+hi)//2; return leaves(v,lo,m)+leaves(v,m,hi)
print('leaves exact b2', leaves(full,0,512))
import collections
print('distinct', len(set(full[128:])))
