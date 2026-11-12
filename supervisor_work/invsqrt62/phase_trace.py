"""Exact basis-state phase trace of an ops.json invsqrt circuit for every x in [1, max_x].

Writes an .npz with: err (int64, phase - target in 2^-64 turns, wrapped), tol (uint64), and
I (uint8 [n_rot, max_x]): whether each non-Clifford/non-T Z_POW fired (control qubit = 1 and op ran),
plus rot_ops (op indices) and rot_units (angle in 2^-64 turns as rounded by the verifier).
HMR outcomes are random (seeded); run twice with different seeds to confirm I and err are outcome-independent.
Usage: python phase_trace.py ops.json out.npz [seed]
"""
import json, sys, math
import numpy as np

d = json.load(open(sys.argv[1])); out = sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
K = d['kinds']; ops = d['ops']; nq = d['n_qubits']; ZP = d['zpow_exact']
MAXX = 3 * (2**10 - 2)**2
M64 = (1 << 64) - 1
HALF = np.uint64(1 << 63)

def units(i):  # verifier: half_turns_to_units, angle in turns = num / 2^128
    n = int(ZP[str(i)])
    return (((n >> 63) + 1) >> 1) & M64   # (turns * 2^64) rounded

def zclass(i):
    n = int(ZP[str(i)])  # turns = n / 2^128; clifford if multiple of 1/4 turn, T if 1/8
    if n % (1 << 126) == 0: return 'c'
    if n % (1 << 125) == 0: return 't'
    return 'r'

rot_ops = [i for i, o in enumerate(ops) if K[o[0]] == 'Z_POW' and zclass(i) == 'r']
ridx = {i: r for r, i in enumerate(rot_ops)}
rot_units = np.array([units(i) for i in rot_ops], dtype=np.uint64)

def reference(xs):
    rs = [math.isqrt((1 << 130) // int(x)) for x in xs]
    target = np.array([((r + 1) >> 1) & M64 for r in rs], dtype=np.uint64)
    tol = np.array([min(r >> 25, 1 << 63) for r in rs], dtype=np.uint64)
    return target, tol

rng = np.random.default_rng(seed)
CH = 1 << 18
ERR = np.zeros(MAXX, np.int64); TOL = np.zeros(MAXX, np.uint64)
I = np.zeros((len(rot_ops), MAXX), np.uint8)
NTOF = np.zeros(MAXX, np.int32)
for s in range(0, MAXX, CH):
    xs = np.arange(s + 1, min(s + CH, MAXX) + 1, dtype=np.int64); N = len(xs)
    q = np.zeros((nq, N), bool)
    for k, qq in enumerate(d['x_qubits']): q[qq] = (xs >> k) & 1
    bits = {}
    B = lambda i: bits.setdefault(i, np.zeros(N, bool))
    ph = np.zeros(N, np.uint64); tof = np.zeros(N, np.int32)
    stack = []; act = np.ones(N, bool)
    for i, o in enumerate(ops):
        k = K[o[0]]
        if k == 'PUSH_CONDITION': stack.append(act); act = act & B(o[1]); continue
        if k == 'POP_CONDITION': act = stack.pop(); continue
        cond = o[-2] if k == 'Z_POW' else o[-1]
        m = act & B(cond) if cond >= 0 else act
        a = o[1:]
        if k == 'X': q[a[0]] ^= m
        elif k == 'CX': q[a[1]] ^= m & q[a[0]]
        elif k == 'CCX': q[a[2]] ^= m & q[a[0]] & q[a[1]]; tof += m
        elif k == 'Z': ph ^= np.where(m & q[a[0]], HALF, np.uint64(0))
        elif k == 'CZ': ph ^= np.where(m & q[a[0]] & q[a[1]], HALF, np.uint64(0))
        elif k == 'CCZ': ph ^= np.where(m & q[a[0]] & q[a[1]] & q[a[2]], HALF, np.uint64(0)); tof += m
        elif k == 'NEG': ph ^= np.where(m, HALF, np.uint64(0))
        elif k == 'CSWAP':
            u, v = q[a[1]], q[a[2]]; sw = m & q[a[0]] & (u != v); u ^= sw; v ^= sw; tof += m
        elif k == 'SWAP':
            u, v = q[a[0]], q[a[1]]; sw = m & (u != v); u ^= sw; v ^= sw
        elif k == 'HMR':
            r = rng.random(N) < 0.5
            ph ^= np.where(m & q[a[0]] & r, HALF, np.uint64(0))
            bb = B(a[1]); bb[m] = r[m]; q[a[0]] &= ~m
        elif k == 'R':
            r = rng.random(N) < 0.5
            ph ^= np.where(m & q[a[0]] & r, HALF, np.uint64(0)); q[a[0]] &= ~m
        elif k == 'BIT_INVERT': B(a[0])[m] ^= True
        elif k == 'BIT_STORE0': B(a[0])[m] = False
        elif k == 'BIT_STORE1': B(a[0])[m] = True
        elif k == 'Z_POW':
            f = m & q[a[0]]
            ph += np.where(f, np.uint64(units(i)), np.uint64(0))
            if i in ridx: I[ridx[i], s:s + N] = f
        else: raise ValueError(k)
    target, tol = reference(xs)
    ERR[s:s + N] = (ph - target).view(np.int64); TOL[s:s + N] = tol; NTOF[s:s + N] = tof
    print(s, file=sys.stderr, flush=True)
np.savez_compressed(out, err=ERR, tol=TOL, I=I, rot_ops=np.array(rot_ops), rot_units=rot_units, ntof=NTOF)
ratio = np.abs(ERR) / TOL.astype(float)
marg = TOL.astype(np.float64) - np.abs(ERR)
print('n_rot ops', len(rot_ops), 'mean fired', I.sum(0).mean(), 'mean tof', NTOF.mean())
print('worst ratio', ratio.max(), 'at x', ratio.argmax() + 1, 'min margin', marg.min(), 'at x', marg.argmin() + 1)
