"""lutpoly17 = lutpoly16 with fan-out-free carry folds (`fold`, `foldA`).

hi += c0 - 2 c1 is done as  c1 ? ~(~hi + v) : hi + v  with the 2-bit source v = [c0, c1 AND NOT c0]
(c1=1: ~(~hi + 2 - c0) = hi - 2 + c0). The CX conjugation of hi by c1 is Clifford; the AND costs
1 Toffoli (init_and) and is measured away (del_and). The old fold needed len(hi)-1 fan-out copies
of c1 as the adder source; now the adder source is 2 qubits + implicit zeros, so the peak drops.
Usage: same flags as lutpoly16.
"""
import os as _os, sys, types
_here = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _here)
src = open(_os.path.join(_here, 'lutpoly14.py')).read()
old_fold = """                    fan = b.alloc_qubits(len(hi) - 1)
                    for q in fan: b.cx(carry[j][1], q)
                    if G: gadd(b, [carry[j][0]] + list(fan), hi, sub=inv)
                    else: (b.isub if inv else b.iadd)(km.array([carry[j][0]] + list(fan)), target=hi)
                    for q in fan: b.cx(carry[j][1], q)
                    b.free(fan)
"""
new_fold = """                    fold2(carry[j][0], carry[j][1], list(hi), inv)
"""
old_A = """                    fan = b.alloc_qubits(len(tg) - 1)
                    for q in fan: b.cx(cA[1], q)
                    gadd(b, [cA[0]] + list(fan), tg, sub=inv)
                    for q in fan: b.cx(cA[1], q)
                    b.free(fan)
"""
new_A = """                    fold2(cA[0], cA[1], tg, inv)
"""
helper = """        def fold2(c0, c1, tg, inv):  # tg += c0 - 2 c1 (inv: -=), no fan-out
            a = b.alloc_qubits(1)[0]
            b.x(c0); b.init_and(c0, c1, a); b.x(c0)
            for q in tg: b.cx(c1, q)
            gadd(b, [c0, a], tg, sub=inv)
            for q in tg: b.cx(c1, q)
            b.x(c0); b.del_and(c0, c1, a); b.x(c0)
            b.free(km.array([a]))

        def horner(inverse):
"""
assert src.count(old_fold) == 1 and src.count(old_A) == 1
src = src.replace(old_fold, new_fold).replace(old_A, new_A).replace("        def horner(inverse):\n", helper, 1)
mod = types.ModuleType('lutpoly14'); mod.__file__ = _os.path.join(_here, 'lutpoly14.py')
sys.modules['lutpoly14'] = mod
exec(compile(src, mod.__file__, 'exec'), mod.__dict__)
sys.argv[0] = _os.path.join(_here, 'lutpoly16.py')
import runpy
runpy.run_path(_os.path.join(_here, 'lutpoly16.py'), run_name='__main__')
