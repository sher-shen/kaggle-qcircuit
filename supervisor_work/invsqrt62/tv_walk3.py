# Supervisor 2026-11-12 04:xx UTC. Plateau walk with pair moves + exact 3->2 merge test (tv_merge3.py algebra).
# Moves keep the network exactly correct: (a) swap gates p, p+1 then re-solve the pair exactly (random solution),
# (b) replace an adjacent pair by a random other exact pair solution.  Every `every` moves: full 3->2 test
# (drop i, re-solve adjacent pair).  On a merge K drops by one and the walk continues.
# Usage: python3 tv_walk3.py in_tv.txt gates.txt seed seconds out_prefix [every]
import sys, random, time
args = sys.argv; sys.argv = args[:3]
exec(open(__file__.replace('tv_walk3.py', 'tv_merge3.py')).read().split("K = len(G)\nif len(sys.argv)")[0])
seed, secs, outp = int(args[3]), float(args[4]), args[5]; every = int(args[6]) if len(args) > 6 else 40
R = random.Random(seed)
def dump(net, tag):
    with open(f'{outp}_k{len(net)}.txt', 'w') as f:
        for L, v, fm in net: f.write(f'{hex(L)} {hex(v)} {fm}\n')
    print(tag, 'K', len(net), 'written', flush=True)
def m3(net):
    for i in range(len(net)):
        rest = net[:i] + net[i + 1:]
        for p in range(len(rest) - 1):
            s = pair_solutions(rest[:p], rest[p + 2:])
            if s: return rest[:p] + list(s[0]) + rest[p + 2:]
    return None
net = list(G); t0 = time.time(); mv = 0; acc = 0
while time.time() - t0 < secs:
    p = R.randrange(len(net) - 1); mv += 1
    if R.random() < 0.5:
        sols = pair_solutions(net[:p], net[p + 2:], first_only=False)  # all (fj,fk,vj,vk,beta) particular solutions
    else:
        n2 = net[:p] + [net[p + 1], net[p]] + net[p + 2:]
        sols = pair_solutions(n2[:p], n2[p + 2:], first_only=False)
    sols = [s for s in sols if s[0][0] and s[1][0]]
    if sols:
        s = R.choice(sols); n2 = net[:p] + list(s) + net[p + 2:]
        if check(n2): net = n2; acc += 1
    if mv % every == 0:
        r = m3(net)
        if r is not None: net = r; assert check(net); dump(net, f'MERGE3 at move {mv}')
        print('move', mv, 'accepted', acc, 'K', len(net), round(time.time() - t0), 's', flush=True)
dump(net, 'final')
