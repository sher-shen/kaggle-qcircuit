"""Mixed Gidney / Cuccaro adder: tgt += src (+cin) mod 2^n, src may be shorter (implicit zeros).
Position i (0 <= i < n-1) produces the carry into i+1:
  'g' (Gidney): init_and into a fresh ancilla (del_and on the way back, measurement-based, free);
       at i = n-2 the carry is XORed straight into the top bit with one CCX (no ancilla).
  'm' (Cuccaro MAJ/UMA): the carry is stored in place in src[i]; costs one extra CCX (the UMA) but no ancilla.
maxanc: positions just below min(m, n-2) are switched to 'm' (top of the source first) until at most maxanc
ancillas are needed."""
import kickmix as km


def gadd_mix(b, src, tgt, cin=None, sub=False, maxanc=None):
    src, tgt = list(src), list(tgt); n, m = len(tgt), len(src)
    assert m <= n
    if n == 0 or (m == 0 and cin is None): return
    if sub: b.x(km.array(tgt))
    mode = ['g'] * max(0, n - 1)
    anc = max(0, n - 2)
    if maxanc is not None:
        for i in range(min(m, n - 2) - 1, 0, -1):
            if anc <= maxanc: break
            mode[i] = 'm'; anc -= 1
    if n == 1:
        if m: b.cx(src[0], tgt[0])
        if cin is not None: b.cx(cin, tgt[0])
        if sub: b.x(km.array(tgt))
        return
    store = [None] * n  # store[i] = qubit holding the carry into position i
    store[0] = cin
    ancs = []
    for i in range(1, n - 1):
        if mode[i - 1] == 'm': store[i] = src[i - 1]
        else:
            q = b.alloc_qubits(1)[0]; ancs.append(q); store[i] = q
    top = tgt[n - 1]
    for i in range(n - 1):
        ci, ai, bi = store[i], (src[i] if i < m else None), tgt[i]
        if mode[i] == 'm':
            b.cx(ai, bi); b.cx(ai, ci); b.ccx(ci, bi, ai)
            continue
        last = i == n - 2
        dst = top if last else store[i + 1]
        mk = b.ccx if last else b.init_and
        if ci is None: mk(ai, bi, dst)
        elif ai is None: mk(bi, ci, dst)
        else:
            b.cx(ci, ai); b.cx(ci, bi); mk(ai, bi, dst); b.cx(ci, dst)
    if n - 1 < m: b.cx(src[n - 1], tgt[n - 1])
    for i in range(n - 2, -1, -1):
        ci, ai, bi = store[i], (src[i] if i < m else None), tgt[i]
        if mode[i] == 'm':
            b.ccx(ci, bi, ai); b.cx(ai, ci); b.cx(ci, bi)
            continue
        last = i == n - 2
        if ci is None:
            if not last: b.del_and(ai, bi, store[1])
            b.cx(ai, bi)
        elif ai is None:
            if not last: b.del_and(bi, ci, store[i + 1])
            b.cx(ci, bi)
        else:
            if not last: b.cx(ci, store[i + 1]); b.del_and(ai, bi, store[i + 1])
            b.cx(ci, ai); b.cx(ai, bi)
    if ancs: b.free(km.array(ancs))
    if sub: b.x(km.array(tgt))
