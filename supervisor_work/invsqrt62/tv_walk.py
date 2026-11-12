# Supervisor 2026-11-12 03:xx UTC. Plateau walk + exact merge test in the transvection model.
# Moves keep the network exactly correct: (a) swap gates j, j+1 and re-solve the gate now at j+1 exactly (tv_merge2 algebra),
# (b) replace gate j by a random exactly-equivalent single transvection (other form / other L on the reachable span).
# Every `every` moves: full 2->1 merge test (drop i, re-solve j). On a merge, K drops by one and the walk continues.
# Usage: python3 tv_walk.py in_tv.txt gates.txt seed seconds out_prefix [every]
import sys, random, time
sys.argv, args = sys.argv[:3], sys.argv
exec(open(__file__.replace('tv_walk.py', 'tv_merge2.py')).read().split("K = len(G); print")[0])
seed, secs, outp = int(args[3]), float(args[4]), args[5]; every = int(args[6]) if len(args) > 6 else 30
R = random.Random(seed)
def options(net, j, drop=None):
    global G
    keep = G; G = net
    try: return best_at(drop if drop is not None else -1, j) if drop is not None else resolve(net, j)
    finally: G = keep
def resolve(net, j):
    # all exact single-gate solutions at position j of net (others fixed); uses best_at with a dummy dropped gate
    global G
    G = [(1, 1, 0)] + net  # dummy gate (never active: form 0) at index 0, dropped
    return [s for s in best_at(0, j + 1)]
def tog(s):
    if s[2] == 'identity': return None
    return (int(s[2], 16), int(s[3], 16), s[4])
def dump(net, tag):
    with open(f'{outp}_k{len(net)}.txt', 'w') as f:
        for L, v, fm in net: f.write(f'{hex(L)} {hex(v)} {fm}\n')
    print(tag, 'K', len(net), 'written', flush=True)
net = list(G); t0 = time.time(); mv = 0; acc = 0
while time.time() - t0 < secs:
    j = R.randrange(len(net)); mv += 1
    if R.random() < 0.6 and j + 1 < len(net):
        n2 = net[:j] + [net[j + 1], net[j]] + net[j + 2:]
        sol = [tog(s) for s in resolve(n2, j + 1)]
        sol = [s for s in sol if s]
        if sol: n2[j + 1] = R.choice(sol); net = n2; acc += 1
        else:
            sol = [tog(s) for s in resolve(n2, j)]; sol = [s for s in sol if s]
            if sol: n2[j] = R.choice(sol); net = n2; acc += 1
    else:
        sol = [s for s in (tog(s) for s in resolve(net, j)) if s]
        if sol: net[j] = R.choice(sol); acc += 1
    if mv % every == 0:
        G = net; hit = None
        for i in range(len(net)):
            for jj in range(len(net)):
                if jj == i: continue
                s = best_at(i, jj)
                if s: hit = (i, jj, s[0]); break
            if hit: break
        if hit:
            i, jj, s = hit; rest = [g for k, g in enumerate(net) if k != i]; q = jj if jj < i else jj - 1
            if s[2] == 'identity': rest.pop(q)
            else: rest[q] = tog(s)
            net = rest; dump(net, f'MERGE at move {mv}')
        print('move', mv, 'accepted', acc, 'K', len(net), round(time.time() - t0), 's', flush=True)
dump(net, 'final')
