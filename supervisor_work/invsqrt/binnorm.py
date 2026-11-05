"""Binary-search normalization: x -> x 4^s with s (0..10) in binary, 4 stages.

Stage r (r = 3..0) sets s_r = [top 2^(r+1) bits of x are zero] with an AND chain over the
negated bits (temporaries erased by measurement right away), then shifts x up by 2^(r+1)
bits with 22 - 2^(r+1) controlled swaps (the top bits are known zero, so a shift suffices).
The inverse un-shifts, recomputes the chain and erases s_r by measurement.
"""


def _and_all(b, bits, target, inverse):
    n = len(bits)
    if n == 1:
        b.cx(bits[0], target); return
    if n == 2:
        (b.del_and if inverse else b.init_and)(bits[0], bits[1], target); return
    tmp = b.alloc_qubits(n - 2)
    b.init_and(bits[0], bits[1], tmp[0])
    for i in range(1, n - 2):
        b.init_and(tmp[i - 1], bits[i + 1], tmp[i])
    (b.del_and if inverse else b.init_and)(tmp[n - 3], bits[n - 1], target)
    for i in range(n - 3, 0, -1):
        b.del_and(tmp[i - 1], bits[i + 1], tmp[i])
    b.del_and(bits[0], bits[1], tmp[0])
    b.free(tmp)


def _stage_flag(b, x, m, flag, inverse):
    top = x[len(x) - m:]
    b.x(top)
    _and_all(b, list(top), flag, inverse)
    b.x(top)


def _shift(b, x, m, ctl, inverse):
    js = list(range(len(x) - m - 1, -1, -1))
    for j in (reversed(js) if inverse else js):
        b.cswap(ctl, x[j], x[j + m])


def normalize(b, x, sb, inverse=False):
    if not inverse:
        for r in (3, 2, 1, 0):
            m = 2 ** (r + 1)
            _stage_flag(b, x, m, sb[r], False)
            _shift(b, x, m, sb[r], False)
    else:
        for r in (0, 1, 2, 3):
            m = 2 ** (r + 1)
            _shift(b, x, m, sb[r], True)
            _stage_flag(b, x, m, sb[r], True)
