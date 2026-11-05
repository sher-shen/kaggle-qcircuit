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
| invsqrt_lut_J.kmb | I + `--binnorm` (binary-search normalization, `binnorm.py`; no thermometer flags / flag packing) | 114 | 1780 | 2032.73 | 231,731.30 | 8.962 | PASS (`verify_lut_J.json`) |
| invsqrt_lut_K.kmb | J + `--zshift` (zero-top shifts in denormalize) | 114 | 1758 | 2010.73 | 229,223.30 | 9.060 | PASS (`verify_lut_K.json`) |
| invsqrt_lut_L.kmb | K + `--droptop` (y's top bit is always 1: not stored during lookup/Horner, a fresh \|1> qubit joins the lane at denormalize) | 113 | 1754 | 2006.73 | 226,760.57 | **9.158** | PASS (`verify_lut_L.json`) |
| invsqrt_lut_N.kmb | **per-segment integer search of (b1,b2)** (`lutpoly7.py`) lets guards 0,-2,-4 pass (model err 2^-23.92 -> 2^-24.15) + `--droprot 1` (no Z_POW on the lowest output bit) | 112 | 1708 | 1960.76 | 219,605.63 | **9.457** | PASS (`verify_lut_N.json`, worst err/tol 0.931) |
| invsqrt_lut_P.kmb | N + `--smallfirst` (denormalize shifts by 1,2,4,8 in that order, so each CSWAP stage only spans the bits that can be occupied: 122 instead of 132 CSWAPs per direction) | 112 | 1688 | 1940.76 | 217,365.63 | 9.554 | PASS (`verify_lut_P.json`, 0.931) |
| invsqrt_lut_Q.kmb | P + `--foldadd` (Horner carry fold `hi += c0 - 2c1` as ONE adder with source bits [c0, c1, c1, ...] via CX fan-out copies of c1, instead of two controlled increments) | 112 | 1648 | 1900.76 | 212,885.63 | **9.755** | PASS (`verify_lut_Q.json`, 0.931) |
| invsqrt_lut_T.kmb | Q + `--round 1,2` (every truncated Horner row adds `(v>>k) + v_{k-1}`, i.e. rounds to nearest, via a carry-in: an extra low target bit `l` set to `v_{k-1}` by CX, `[l, acc] += [v_{k-1}, src]` leaves `l = 0`; `l` borrows an unused pad qubit when one is free) lets coarser guards 0,-3,-5 pass (model err 2^-24.14), `--pad 7 --maxq 111` | 111 | 1646 | 1896.24 | 210,482.92 | **9.867** | PASS (`verify_lut_T.json`, 0.906) |

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
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --zshift --out K.kmb   # = invsqrt_lut_K.kmb
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --zshift --droptop --out L.kmb   # = invsqrt_lut_L.kmb (current best)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --guards=0,-2,-4 --pad 6 --clamp --binnorm --zshift --droptop --droprot 1 --out N.kmb   # = invsqrt_lut_N.kmb (current best, ~25 s)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --guards=0,-2,-4 --pad 6 --clamp --binnorm --zshift --droptop --droprot 1 --smallfirst --foldadd --out Q.kmb   # = invsqrt_lut_Q.kmb (drop --foldadd for P)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --clamp --binnorm --zshift --droptop --droprot 1 --smallfirst --foldadd --guards=0,-3,-5 --round 1,2 --pad 7 --maxq 111 --out T.kmb   # = invsqrt_lut_T.kmb (current best, sha e8f2d083)
python3.13 supervisor_work/invsqrt/make_cand.py OUT.kmb 13,17,27,28,28 1 1   # old NR candidate B
```
`data/kickmix/kickmix.so` is a CPython 3.13 Linux x86 build. Needs numpy + scipy.

## Experiments that did not beat L (2026-11-05 03:xx run)
- `--maxq N` (kickmix trades adder ancillas for Toffolis, about +1 Toffoli per adder per qubit): 114→110 q costs +82 Toffoli, 105 q +212; worse S.
- `lutpoly5.py` (M in [1,2), 5 shift stages, parity e in a 256-entry address, x[21] borrowed as pad): lookup 383→254, but the 14th Horner row
  pushes the error to 2^-23.97 at guards 0,-1,-4 (fails); guards 0,0,-4 gives 2^-24.31 but 114 q / 1755 Toffoli. Kept for later (needs a precision fix).

## 2026-11-05 04:xx run
- `lutpoly6.py` = lutpoly4 + `--droprot m` (+ `main()` wrapper, clamp loop reordered; old outputs byte-identical, L rebuilt = 9ce35e85).
  L+droprot1: 9.187x (err/tol 0.833); L+droprot2: 9.190x (0.937). All PASS, full run.
- `lutpoly7.py`: for each (d1,d2) in [-3,3]^2 runs the exact integer model on all x_norm and keeps per segment the offset with the
  smallest relative-error spread; a0 then re-centred. guards 0,-2,-4: 112 q / 1708 Toffoli, verifier 9.432x (0.904); +droprot1 9.457x (0.931).
  R=6 gives no further gain; the worst segments are at M~3-4 (truncation noise, y < 2^28.x there), not at M~1.
- **lutpoly5.py is wrong with `--rangeq`**: all 512 addresses (e, mantissa) are reachable there but rangeq skips 0..127
  (e=0, M<1.5); verifier fails at x=2. Without rangeq it needs k=8 to save lookup, which gives 114 q / 1755 (no gain). Dropped.
- fy=28 cannot pass even with precise r/c2 (guards 0,2,2: 2^-23.80): the y-step truncation noise is the limit.

## 2026-11-05 05:xx run
- Toffoli breakdown of N (flame chart): normalize 78 / lookup 354 / Horner 395 / denormalize 122 / phase (35 rotations) / denormalize_inv 122 /
  Horner_inv 395 / unlookup 38 / normalize_inv 74. Peak 112 q is inside the y-step row adders (x 22 + s 4 + y 28 + r 18 + b2 8 + pad 6 + carries 4 + adder ancilla ~22).
- `--smallfirst` (P, 9.554x) and `--foldadd` (Q, 9.755x): both value-identical to N (same worst err/tol 0.9305), full verifier PASS. lutpoly6 old outputs still byte-identical (N rebuilt = ee3f21fc).
- pad sweep with P+Q flags: pad 4/5/6/7/8 -> 110q 1692 / 111q 1668 / 112q 1648 / 113q 1632 / 114q 1620 Toffoli; pad 6 still best.
