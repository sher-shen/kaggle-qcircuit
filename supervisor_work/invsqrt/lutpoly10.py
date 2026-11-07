"""lutpoly10: non-uniform segments (supervisor, 2026-11-07).

Relative error of a quadratic piece scales like h^3 M^-3, so for M in [2,4) a segment twice as wide
is no worse than the M ~ 1 segments. Horner signed digits are the low D = 14 bits of x_norm for every
x; the table is indexed by x_norm[13:22] (9 bits). For M < 2, x[13] is both an address bit and the top
signed digit (each 9-bit segment is fit on its half of the digit window); for M >= 2 the two table rows
of a pair are identical. Lookup = one unary iteration over x[14:22] (192 values) plus, for the 64 values
with M < 2, a nested 1-bit iteration on x[13]: ~256 Toffoli instead of 383. Cost: one more Horner row
per step and wider b1/b2 registers. Code: lutpoly6nu.py / lutpoly7nu.py (generated from lutpoly6/7).
"""
import os as _os, sys
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import lutpoly7nu

if __name__ == '__main__':
    lutpoly7nu.Design.search = True
    lutpoly7nu.base.main(lutpoly7nu.Design)
