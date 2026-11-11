"""Driver for dc3.c: exact 'K Toffolis + affine' test on the reachable set D (default K = 3, i.e. 4 -> 3).
Usage: block_dc3.py dc3_bin blocks.json idx ops.json [nproc]  |  --plant dc3_bin blocks.json idx seed [nproc]"""
import sys, json, subprocess, random
def sim(b, ops, kinds, x):
    W = b['W']; pos = {q: i for i, q in enumerate(W)}; bit = lambda q: (x >> pos[q]) & 1
    for i in b['ops']:
        o = ops[i]; k = kinds[o[0]]
        if k == 'X': x ^= 1 << pos[o[1]]
        elif k == 'CX':
            if bit(o[1]): x ^= 1 << pos[o[2]]
        elif k == 'CCX':
            if bit(o[1]) and bit(o[2]): x ^= 1 << pos[o[3]]
        elif k == 'SWAP':
            a, c = bit(o[1]), bit(o[2])
            if a != c: x ^= (1 << pos[o[1]]) | (1 << pos[o[2]])
        elif k == 'CSWAP':
            if bit(o[1]):
                a, c = bit(o[2]), bit(o[3])
                if a != c: x ^= (1 << pos[o[2]]) | (1 << pos[o[3]])
        else: raise SystemExit('op %s' % k)
    return x
def run(cbin, n, pts, nproc):
    inp = '%d %d\n' % (n, len(pts)) + ''.join('%d %d\n' % p for p in pts)
    ps = [subprocess.Popen([cbin, str(k), str(nproc)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for k in range(nproc)]
    for p in ps: p.stdin.write(inp); p.stdin.close()
    hits = []; tested = 0
    for p in ps:
        hits += [l for l in p.stdout.read().split('\n') if l.startswith('HIT')]
        tested += int(p.stderr.read().split('tested')[1].split()[0]); p.wait()
    return tested, hits
if __name__ == '__main__':
    if sys.argv[1] == '--plant':
        cbin, bf, bi, seed = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]); nproc = int(sys.argv[6]) if len(sys.argv) > 6 else 4
        b = json.load(open(bf))[bi]; n = len(b['W']); rnd = random.Random(seed); S = 1 << n
        par = lambda v: bin(v).count('1') & 1
        def rgate():
            while True:
                l1, l2 = rnd.randrange(1, S), rnd.randrange(1, S)
                if l1 == l2: continue
                vs = [v for v in range(1, S) if not par(l1 & v) and not par(l2 & v)]
                v = rnd.choice(vs); c1, c2 = rnd.randrange(2), rnd.randrange(2)
                return lambda x: x ^ v if par(l1 & x) == c1 and par(l2 & x) == c2 else x
        gs = [rgate() for _ in range(3)]
        while True:
            rows = [rnd.randrange(S) for _ in range(n)]; img = {sum(par(r & x) << k for k, r in enumerate(rows)) for x in range(S)}
            if len(img) == S: break
        a0 = rnd.randrange(S)
        A = lambda y: sum(par(r & y) << k for k, r in enumerate(rows)) ^ a0
        def P(x):
            for g in gs: x = g(x)
            return A(x)
        tested, hits = run(cbin, n, [(x, P(x)) for x in b['reach']], nproc)
        print('plant seed', seed, 'block', bi, 'n', n, '|D|', len(b['reach']), 'tested', tested, 'HIT' if hits else 'NONE', hits[:2], flush=True); sys.exit()
    cbin, bf, bi, of = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]; nproc = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    d = json.load(open(of)); b = json.load(open(bf))[bi]; n = len(b['W'])
    pts = [(x, sim(b, d['ops'], d['kinds'], x)) for x in b['reach']]
    tested, hits = run(cbin, n, pts, nproc)
    print(bi, 'ops', b['ops'][0], '..', b['ops'][-1], 'n', n, 'tof', b['tof'], '|D|', len(b['reach']), 'K 3 tested', tested,
          ('HIT(candidate) %s' % hits[:3]) if hits else 'NONE(exact, K=3 on D)', flush=True)
