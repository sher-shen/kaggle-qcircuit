"""Supervisor variant of the official reference NR circuit: lazy allocation, c3 unload, optional square drop."""
import os as _os; ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
import sys, math, dataclasses
sys.path.insert(0, ROOT + '/data/kickmix')
sys.path.insert(0, ROOT + '/data/verifiers/invsqrt')
import kickmix as km
import nr_reference_circuit as nr
from nr_reference_circuit import (_normalize, _select_interval, _load_coefficients, _add_row, _square,
                                  _multiply_m, _correct, _multiply_y0, _denormalize, _phase_by_bits, Precision)

def _load_one(b, prec, x, selectors, j, reg):
    top, t_a, t_b = x[len(x) - 1], selectors[0], selectors[1]
    table = prec.coefficient_table()
    for control, value in ((True, table[0][j]), (top, table[0][j] ^ table[2][j]),
                           (t_a, table[0][j] ^ table[1][j]), (t_b, table[2][j] ^ table[3][j])):
        b.gf2_iadd(value, target=reg, control=control)

def _hstep(b, inverse, prec, x, selectors, acc, mult, scratch):
    width, wc = len(x), len(acc)
    delta = [(selectors[2], 1)] + [(x[width - 2 - m], m) for m in range(2, min(prec.delta_bits, width - 2) + 1)]
    for control, m in delta:
        _add_row(b, inverse, control, [(mult[i], i - m) for i in range(m, wc)], acc, scratch, subtract=True)

def build(n_p=10, prec=Precision(), drop_square=False, drop_horner=False):
    width = 2 * n_p + 2
    out_bits = prec.output_bits(n_p)
    b = km.CircuitBuilder()
    x = b.create_quantum_register(width, name='x')
    flags, selectors = b.alloc_qubits(n_p), b.alloc_qubits(3)
    sw = max(prec.square_bits, prec.product_bits + 2, prec.result_bits + 1)
    scratch = b.alloc_qubits(sw)
    wc = prec.coef_bits
    c0, c1, c2 = (b.alloc_qubits(wc) for _ in range(3))

    def front(inverse):
        # normalize / select / load c0..c2 / horner with temporary c3
        if not inverse:
            _normalize(b, False, x, flags); _select_interval(b, False, x, selectors)
            for j, r in enumerate((c0, c1, c2)): _load_one(b, prec, x, selectors, j, r)
            c3 = b.alloc_qubits(wc); _load_one(b, prec, x, selectors, 3, c3)
            _hstep(b, False, prec, x, selectors, c2, c3, scratch)
            _load_one(b, prec, x, selectors, 3, c3); b.free(c3)
            _hstep(b, False, prec, x, selectors, c1, c2, scratch)
            _hstep(b, False, prec, x, selectors, c0, c1, scratch)
        else:
            _hstep(b, True, prec, x, selectors, c0, c1, scratch)
            _hstep(b, True, prec, x, selectors, c1, c2, scratch)
            c3 = b.alloc_qubits(wc); _load_one(b, prec, x, selectors, 3, c3)
            _hstep(b, True, prec, x, selectors, c2, c3, scratch)
            _load_one(b, prec, x, selectors, 3, c3); b.free(c3)
            for j, r in enumerate((c0, c1, c2)): _load_one(b, prec, x, selectors, j, r)
            _select_interval(b, True, x, selectors); _normalize(b, True, x, flags)

    front(False)
    y0 = c0
    def strip(inverse):
        # free r2 (in c1) and r1 (in c2) once y0 is known; inverse re-creates them
        if not inverse:
            _hstep(b, True, prec, x, selectors, c1, c2, scratch)          # r2 -> c1
            _load_one(b, prec, x, selectors, 1, c1)                      # c1 -> 0
            c3 = b.alloc_qubits(wc); _load_one(b, prec, x, selectors, 3, c3)
            _hstep(b, True, prec, x, selectors, c2, c3, scratch)          # r1 -> c2
            _load_one(b, prec, x, selectors, 3, c3); b.free(c3)
            _load_one(b, prec, x, selectors, 2, c2)
        else:
            _load_one(b, prec, x, selectors, 2, c2)
            c3 = b.alloc_qubits(wc); _load_one(b, prec, x, selectors, 3, c3)
            _hstep(b, False, prec, x, selectors, c2, c3, scratch)
            _load_one(b, prec, x, selectors, 3, c3); b.free(c3)
            _load_one(b, prec, x, selectors, 1, c1)
            _hstep(b, False, prec, x, selectors, c1, c2, scratch)
    if drop_horner:
        strip(False); b.free(c1); b.free(c2)
    square = b.alloc_qubits(prec.square_bits)
    _square(b, False, y0, square, scratch)
    z = b.alloc_qubits(prec.product_bits + 2)
    _multiply_m(b, False, x, square, z, scratch)
    if drop_square:
        _square(b, True, y0, square, scratch); b.free(square)
    _correct(b, False, z)
    y1 = b.alloc_qubits(out_bits)
    p = y1[:len(y1) - len(flags)]
    _multiply_y0(b, False, y0, z, p, scratch)
    _denormalize(b, False, flags, y1)
    _phase_by_bits(b, y1)
    _denormalize(b, True, flags, y1)
    _multiply_y0(b, True, y0, z, p, scratch)
    b.free(y1)
    _correct(b, True, z)
    if drop_square:
        square = b.alloc_qubits(prec.square_bits)
        _square(b, False, y0, square, scratch)
    _multiply_m(b, True, x, square, z, scratch)
    b.free(z)
    _square(b, True, y0, square, scratch)
    b.free(square)
    if drop_horner:
        c1 = b.alloc_qubits(wc); c2 = b.alloc_qubits(wc)
        strip(True)
    front(True)
    for r in (c0, c1, c2, scratch, flags, selectors): b.free(r)
    return b.finish_circuit()

if __name__ == '__main__':
    for ds in (False, True):
        c = build(drop_square=ds)
        print('drop_square', ds, c.num_qubits, c.operation_statistics().num_toffoli_like)
    if len(sys.argv) > 1:
        build(drop_square=sys.argv[2] == '1').to_file(sys.argv[1], format='kmb')
