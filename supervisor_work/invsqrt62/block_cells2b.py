"""block_cells2 with the exact per-cell survivor test moved into C (cells2b.c), for m = 20 blocks (~1.6M survivors).
Same necessary condition as block_cells2.py.  Usage: block_cells2b.py cells2b_bin blocks.json idx [nproc ops.json]
                                                     | --plant cells2b_bin blocks.json idx kind seed"""
import sys, json, subprocess
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import block_cells2 as C2
def test(Y, f, cbin, nproc=4):
    m = Y.shape[1]; Yi = (Y.astype(np.int64) * (1 << np.arange(m))).sum(1).tolist()
    Q = C2.quads(Yi, f)
    inp = '%d %d\n' % (m, len(Q)) + ''.join('%d %d\n' % q for q in Q) + '%d\n' % len(Yi) + ''.join('%d %d\n' % (y, int(v)) for y, v in zip(Yi, f))
    ps = [subprocess.Popen([cbin, str(k), str(nproc)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for k in range(nproc)]
    for p in ps: p.stdin.write(inp); p.stdin.close()
    hits = []; ns = 0
    for p in ps:
        hits += [tuple(map(int, l.split()[1:])) for l in p.stdout.read().split('\n') if l.startswith('HIT')]
        ns += int(p.stderr.read().split()[1]); p.wait()
    return len(Q), ns, hits
C2.test = test
if __name__ == '__main__':
    if sys.argv[1] == '--plant':
        sys.argv = sys.argv[:1] + sys.argv[1:]
    exec(open(C2.__file__).read().split("if __name__ == '__main__':", 1)[1].replace('\n    ', '\n'), {**C2.__dict__, 'test': test, 'sys': sys})
