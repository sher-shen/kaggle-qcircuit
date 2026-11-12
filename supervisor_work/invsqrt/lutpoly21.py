"""lutpoly21 = lutpoly18 with --binnorm using binnorm2 (one prefix AND chain for all four s bits)."""
import os as _os, sys, runpy
H = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, H)
import lutpoly14oc, binnorm2
lutpoly14oc.binnorm = binnorm2
sys.modules['lutpoly14'] = lutpoly14oc
runpy.run_path(_os.path.join(H, 'lutpoly16.py'), run_name='__main__')
