"""lutpoly22 = lutpoly21 with binnorm3 (s erased by X-measurement + conditional phase fixup)."""
import os as _os, sys, runpy
H = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, H)
import lutpoly14oc, binnorm3
lutpoly14oc.binnorm = binnorm3
sys.modules['lutpoly14'] = lutpoly14oc
runpy.run_path(_os.path.join(H, 'lutpoly16.py'), run_name='__main__')
