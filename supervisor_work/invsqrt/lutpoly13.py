"""lutpoly13 = lutpoly11 with --topccx: the Gidney adder's last carry (into the top target bit) is not
stored in an ancilla; it is XORed straight into the top bit with one CCX (same Toffoli count as the
init_and it replaces, del_and side becomes free). Every adder needs n-2 instead of n-1 ancillas, so
the Horner peak drops by one qubit at no Toffoli cost. Also adds --groups (see lutpoly14)."""
import os as _os, sys
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import lutpoly11 as L
km = L.km


def gadd_top(b, src, tgt, cin=None, sub=False):
    """Same arithmetic as lutpoly11.gadd (tgt += src + cin mod 2^n), n-2 ancillas."""
    src, tgt = list(src), list(tgt); n, m = len(tgt), len(src)
    assert m <= n
    if n == 0 or (m == 0 and cin is None): return
    if n <= 2:
        return L._gadd_orig(b, src, tgt, cin, sub)
    if sub: b.x(km.array(tgt))
    top = tgt[n - 1]
    c = [None] + list(b.alloc_qubits(n - 2)) + [None]   # c[n-1] is never stored
    def cq(i): return cin if i == 0 else c[i]
    for i in range(n - 1):
        ci, ai, bi = cq(i), (src[i] if i < m else None), tgt[i]
        last = i == n - 2
        dst = top if last else c[i + 1]
        mk = b.ccx if last else b.init_and
        if ci is None: mk(ai, bi, dst)
        elif ai is None: mk(bi, ci, dst)
        else:
            b.cx(ci, ai); b.cx(ci, bi); mk(ai, bi, dst); b.cx(ci, dst)
    if n - 1 < m: b.cx(src[n - 1], tgt[n - 1])
    for i in range(n - 2, -1, -1):
        ci, ai, bi = cq(i), (src[i] if i < m else None), tgt[i]
        last = i == n - 2
        if ci is None:
            if not last: b.del_and(ai, bi, c[1])
            b.cx(ai, bi)
        elif ai is None:
            if not last: b.del_and(bi, ci, c[i + 1])
            b.cx(ci, bi)
        else:
            if not last: b.cx(ci, c[i + 1]); b.del_and(ai, bi, c[i + 1])
            b.cx(ci, ai); b.cx(ai, bi)
    b.free(km.array(c[1:n - 1]))
    if sub: b.x(km.array(tgt))


L._gadd_orig = L.gadd
if '--topccx' in sys.argv:
    sys.argv.remove('--topccx')
    L.gadd = gadd_top

if __name__ == '__main__':
    L.SDesign.search = True
    L.main(L.SDesign)
