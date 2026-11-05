# invsqrt — supervisor work branch

Own code only (no third-party notebook code). Nothing here was submitted to Kaggle.

## Results (official verifier `data/verifiers/invsqrt/verify_submission_invsqrt.py`, 200,540,928 shots, default salt, 4-core Linux)
| file | design | Q | Toffoli | C | cost (Q·C) | × ref | verifier |
|---|---|---|---|---|---|---|---|
| reference | NR (official) | 260 | 7735 | 7987.59 | 2,076,774.23 | 1.000 | PASS |
| invsqrt_sv_A.kmb | NR, precision search + lazy alloc | 212 | 8281 | 8530.53 | 1,808,472.20 | 1.148 | PASS |
| invsqrt_sv_B.kmb | A + drop Horner intermediates | 178 | 9633 | 9882.53 | 1,759,090.20 | 1.181 | PASS |
| invsqrt_lut_C.kmb | **LUT + quadratic, no Newton** (`lutpoly.py --binshift --fy 28 --guards 0,1,1`) | 152 | 2853 | 3093.23 | 470,171.25 | 4.417 | PASS (`verify_lut_C.json`) |
| invsqrt_lut_D.kmb | C + reachable-address QROM + packed flags (`--packflags --rangeq --fy 28 --guards 0,1,1`) | 146 | 2746 | 2986.23 | 435,989.86 | **4.763** | PASS (`verify_lut_D.json`) |

## LUT design (`lutpoly.py`)
1. Normalize `x -> x_norm = x 4^s` (official reference routine), `M = x_norm/2^20 in [1,4)`.
2. Optional `--packflags` (`flagpack.py`): thermometer flags (10 q) -> binary `s` (4 q) with a CX network
   plus 10 Toffolis; reversed before the inverse normalize. Exhaustively tested for s = 0..10.
3. QROM on the top k=9 bits of `x_norm` loads `(a0, b1, b2)` for 384 reachable segments
   (`--rangeq`: unary iteration over `range(128, 512)` instead of `init_lookup` over 512).
4. Horner in place: `r = b1 - T(b2 t)`, `y = a0 - T(r t)`, `t` = low 13 bits of `x_norm`, rows via reference `_add_row`.
   Coefficients: Chebyshev-node quadratic fit per segment, then `a0` re-centred with the exact integer model.
   Worst model error over all x in [1, max_x]: 2^-24.73 (verifier worst err/tol 0.603).
5. Denormalize `y1 = y 2^s` with four controlled rotations by 8,4,2,1 (`--binshift`), Z_POW per bit, uncompute all.

## Reproduce
```
python3.13 supervisor_work/invsqrt/lutpoly.py --packflags --rangeq --fy 28 --guards 0,1,1 --out D.kmb   # byte-identical to invsqrt_lut_D.kmb
PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py D.kmb             # ~6 min on 4 cores
python3.13 supervisor_work/invsqrt/make_cand.py OUT.kmb 13,17,27,28,28 1 1   # old NR candidate B
```
`data/kickmix/kickmix.so` is a CPython 3.13 Linux x86 build. Needs numpy + scipy.
