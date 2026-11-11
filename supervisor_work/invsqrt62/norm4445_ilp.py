import itertools
cases={'A':(1,0,0),'B':(0,1,0),'C':(1,1,0),'D':(0,0,1),'E':(1,0,1)}
need={'A':10,'B':14,'C':9,'D':6,'E':3}
gens=[]
for a,b,c,dd in itertools.product((0,1),repeat=4):
    if (a,b,c)==(0,0,0): continue
    if dd: continue   # constant term would act on case 0 (identity) -> skip
    act=[k for k,(x,y,z) in cases.items() if (a*x+b*y+c*z+dd)%2]
    gens.append(((a,b,c),act))
best=None
R=range(0,15)
import sys
for xs in itertools.product(R,repeat=len(gens)):
    s=sum(xs)
    if best and s>=best[0]: continue
    tot={k:0 for k in cases}
    for x,(g,act) in zip(xs,gens):
        for k in act: tot[k]+=x
    if all(tot[k]>=need[k] for k in cases): best=(s,xs)
print(best,[g for g,_ in gens])
