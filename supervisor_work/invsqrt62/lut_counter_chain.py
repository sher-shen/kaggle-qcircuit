import sys,numpy as np
F=np.load(sys.argv[1]).astype(int)  # 35x256
W=[22,24]+list(range(29,62))
# toggles within each half
def tog(f,half):
    s=f[half*128:(half+1)*128]; return np.nonzero(s[1:]!=s[:-1])[0]
for h in (0,1):
    print('half',h)
    for i,w in enumerate(W):
        t=tog(F[i],h); print(w,len(t),end='; ')
    print()
# carry relation: hi toggles only where lo toggles (lo 1->0 for inc, or 0->1 for dec)
for h in (0,1):
  rel=[]
  for i,wl in enumerate(W):
    tl=set(tog(F[i],h))
    for j,wh in enumerate(W):
        if i==j: continue
        th=set(tog(F[j],h))
        if th and th<=tl and len(th)<len(tl): rel.append((wh,wl,len(th),len(tl)))
  print('half',h,'hi<=lo toggles:',rel)
