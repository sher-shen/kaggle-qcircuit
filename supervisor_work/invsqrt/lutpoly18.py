"""lutpoly18 = lutpoly16 (s-aware search, mixed adders) built on lutpoly14oc (--onecarry: one carry qubit per
Horner window, offsets loaded by the lookup). Same flags as lutpoly16 plus --onecarry."""
import os as _os, sys, runpy
H = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, H)
if '--topccx' in sys.argv:  # lutpoly14oc consumes it at import
    pass
import lutpoly14oc
sys.modules['lutpoly14'] = lutpoly14oc
runpy.run_path(_os.path.join(H, 'lutpoly16.py'), run_name='__main__')
