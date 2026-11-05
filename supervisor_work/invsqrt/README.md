# invsqrt — supervisor work branch

Own code only (no third-party notebook code). Nothing here was submitted to Kaggle.

## Results (official verifier `data/verifiers/invsqrt/verify_submission_invsqrt.py`, 200,540,928 shots, default salt, 4-core Linux)
| file | design | Q | Toffoli | C | cost (Q·C) | × ref | verifier |
|---|---|---|---|---|---|---|---|
| reference | NR (official) | 260 | 7735 | 7987.59 | 2,076,774.23 | 1.000 | PASS |
| invsqrt_sv_A.kmb | NR, precision search + lazy alloc | 212 | 8281 | 8530.53 | 1,808,472.20 | 1.148 | PASS |
| invsqrt_sv_B.kmb | A + drop Horner intermediates | 178 | 9633 | 9882.53 | 1,759,090.20 | 1.181 | PASS |
| invsqrt_lut_C.kmb | **LUT + quadratic, no Newton** (`lutpoly.py --binshift --fy 28 --guards 0,1,1`) | 152 | 2853 | 3093.23 | 470,171.25 | 4.417 | PASS (`verify_lut_C.json`) |
| invsqrt_lut_D.kmb | C + reachable-address QROM + packed flags (`--packflags --rangeq --fy 28 --guards 0,1,1`) | 146 | 2746 | 2986.23 | 435,989.86 | 4.763 | PASS (`verify_lut_D.json`) |
| invsqrt_lut_E.kmb | D + trimmed denormalize lanes (current `lutpoly.py`, same flags as D) | 146 | 2728 | 2968.23 | 433,361.86 | 4.792 | PASS (`verify_lut_E.json`) |
| invsqrt_lut_H.kmb | **signed-digit δ + windowed Horner** (`lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6`) | 115 | 1884 | 2136.73 | 245,724.03 | 8.452 | PASS (`verify_lut_H.json`) |
| invsqrt_lut_I.kmb | H + `--clamp` (y < 2^fy, y register 29 bits) | 114 | 1866 | 2118.73 | 241,535.30 | 8.598 | PASS (`verify_lut_I.json`) |
| invsqrt_lut_J.kmb | I + `--binnorm` (binary-search normalization, `binnorm.py`; no thermometer flags / flag packing) | 114 | 1780 | 2032.73 | 231,731.30 | **8.962** | PASS (`verify_lut_J.json`) |

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

## Signed-digit + windowed Horner (`lutpoly3.py`, `lutpoly4.py`) — candidate H
- Offset digits are read as ±1: δ = (2t+1-2^D)/2^D = Σ (2d_i-1) 2^(i-D). The quadratic is fit on δ∈(-1,1) (centred segment).
  Each Horner row `acc -= (2d_i-1)·v` is `CX(d_i→acc); acc += v; CX(d_i→acc)` (d=1: ~(~acc+v) = acc-v). No AND layer, no
  scratch register (Q 146 → 132 in `lutpoly3.py`); a small zero pad (`--pad`) extends short sources so adders avoid the
  costly increment tail.
- `lutpoly4.py`: rows add only into the low `L_j` bits of the accumulator plus 2 signed carry qubits (value range checked
  exactly over all x_norm in `choose_L`), then the carries are folded into the high part once (`hi += c0`, `hi[1:] -= c1`).
  Arithmetic is identical to the unwindowed version (same model, same error); y-step adders shrink 30→22 bits, r-step 19→13.
- `--binnorm` (`binnorm.py`): 4 stages r=3..0, s_r = [top 2^(r+1) bits zero] by an AND chain over the negated bits
  (temporaries erased by measurement at once), then a zero-top shift by 2^(r+1) bits with 22-2^(r+1) CSWAPs; gives s in
  binary directly. Forward 84 Toffoli, inverse ~80 (chain recomputed, s_r erased by measurement), vs 120+120+20 before.
- `--zshift`: denormalize lanes use zero-top shifts (CSWAP chain) instead of rotations (-22 Toffoli).
- `--clamp`: y < 2^fy (re-centred a0 for the M≈1 segment), so y needs fy bits instead of fy+1 (candidate I, see SUPERVISOR.md).

## Reproduce
```
python3.13 supervisor_work/invsqrt/lutpoly.py --packflags --rangeq --fy 28 --guards 0,1,1 --out E.kmb   # byte-identical to invsqrt_lut_E.kmb
PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py E.kmb             # ~6 min on 4 cores
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --out H.kmb   # byte-identical to invsqrt_lut_H.kmb
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --out J.kmb   # = invsqrt_lut_J.kmb
python3.13 supervisor_work/invsqrt/make_cand.py OUT.kmb 13,17,27,28,28 1 1   # old NR candidate B
```
`data/kickmix/kickmix.so` is a CPython 3.13 Linux x86 build. Needs numpy + scipy.
