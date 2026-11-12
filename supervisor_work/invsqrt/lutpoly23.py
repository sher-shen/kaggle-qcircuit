"""lutpoly23 = lutpoly21 with binnorm4 (per-stage X-measurement of s right after its un-shift)."""
import os as _os, sys, runpy
H = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, H)
import lutpoly14oc, binnorm4
lutpoly14oc.binnorm = binnorm4
sys.modules['lutpoly14'] = lutpoly14oc
runpy.run_path(_os.path.join(H, 'lutpoly16.py'), run_name='__main__')
