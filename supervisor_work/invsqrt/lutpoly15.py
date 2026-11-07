"""lutpoly15 = lutpoly14 with every Horner/fold adder built by gadd_mix.gadd_mix(maxanc=N) (`--maxanc N`):
the top source positions use in-place Cuccaro MAJ/UMA carries (+1 CCX each, no ancilla) until the adder
needs at most N ancillas. Without --maxanc it is identical to lutpoly14 --topccx."""
import os as _os, sys
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
mx = None
if '--maxanc' in sys.argv:
    k = sys.argv.index('--maxanc'); mx = int(sys.argv[k + 1]); del sys.argv[k:k + 2]
if '--topccx' in sys.argv: sys.argv.remove('--topccx')
import lutpoly14 as P
from gadd_mix import gadd_mix
P.gadd = lambda b, src, tgt, cin=None, sub=False: gadd_mix(b, src, tgt, cin, sub, mx)

if __name__ == '__main__':
    P.SDesign.search = True
    P.main(P.SDesign)
