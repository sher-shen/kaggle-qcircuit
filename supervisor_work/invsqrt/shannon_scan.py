import pickle, sys
d = pickle.load(open(sys.argv[1], 'rb')); T = d['table']; na, nt = d['na'], d['nt']
print('addr bits', na, 'target bits', nt, 'distinct', len(set(T[128:512])))
lo, hi = 128, 512
# for each node (height h, prefix p) inside [lo,hi): children = p*2^h + [0,2^(h-1)) and +2^(h-1)
tot = 0
for h in range(1, na + 1):
    half = 1 << (h - 1); cnt = 0; ok = 0; sav = 0
    for p in range(0, 1 << (na - h)):
        base = p << h
        if base < lo or base + (1 << h) > hi: continue
        cnt += 1
        D = {T[base + i] ^ T[base + half + i] for i in range(half)}
        if len(D) == 1: ok += 1; sav += half - 1
        # number of distinct differences (rank-ish measure)
    print(f'h={h} nodes={cnt} const-diff={ok} save~{sav}')
# per output bit: how many bits are affine in address bit j globally across reachable range
for j in range(na):
    m = 1 << j; good = 0
    for b in range(nt):
        s = set()
        for v in range(lo, hi):
            if (v & m) == 0 and lo <= (v | m) < hi:
                s.add(((T[v] >> b) ^ (T[v | m] >> b)) & 1)
        if len(s) == 1: good += 1
    print('addr bit', j, 'output bits with constant derivative', good)
