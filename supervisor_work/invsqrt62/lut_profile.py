import numpy as np,sys
F=np.load(sys.argv[1])
def anfdeg(t):
    t=list(t)
    for i in range(8):
        for a in range(256):
            if a>>i&1: t[a]^=t[a^(1<<i)]
    return max([bin(m).count('1') for m in range(256) if t[m]]+[0])
for k,f in enumerate(F): print(k,'toggles',int((f[1:128]!=f[:127]).sum()),int((f[129:]!=f[128:255]).sum()),'deg',anfdeg(f))
