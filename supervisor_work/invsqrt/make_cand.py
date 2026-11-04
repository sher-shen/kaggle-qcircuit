import sys
import os as _os; ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/data/kickmix'); sys.path.insert(0, ROOT + '/data/verifiers/invsqrt')
import nr_reference_circuit as nr, variant, hashlib
t = tuple(int(v) for v in sys.argv[2].split(','))
c = variant.build(prec=nr.Precision(*t), drop_square=sys.argv[3] == '1', drop_horner=len(sys.argv) > 4 and sys.argv[4] == '1')
c.to_file(sys.argv[1], format='kmb')
print(sys.argv[1], c.num_qubits, c.operation_statistics().num_toffoli_like, hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()[:16])
