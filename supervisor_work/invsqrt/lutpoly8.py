"""lutpoly8 = lutpoly5 (M in [1,2), 256-entry lookup) + the per-segment (b1, b2) local search of lutpoly7."""
import os as _os, sys
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import numpy as np
import lutpoly5 as base
from lutpoly7 import Search


class Design(Search, base.Design):
    def search_domain(self):
        xn = np.arange(0, 2**22, dtype=np.int64)
        exact = 2.0**self.fy * 2.0**(((xn >> 21) - 1) / 2) / np.sqrt(1 + (xn & (2**21 - 1)) / 2.0**21)
        return xn, exact


if __name__ == '__main__':
    Design.search = True
    if '--R' in sys.argv:
        i = sys.argv.index('--R'); Design.R = int(sys.argv[i + 1]); del sys.argv[i:i + 2]
    base.main(Design)
