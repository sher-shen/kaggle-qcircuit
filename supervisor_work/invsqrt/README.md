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
| invsqrt_lut_U.kmb | T's rounding carried to **fy=28**: `--fy 28 --guards=0,-2,-4 --round 1,2 --droprot 0 --pad 7 --maxq 110` (y 28 bits, model err 2^-24.01, tiny margin so rotation eps 5.5e-14) | 110 | 1604 | 1866.49 | 205,313.67 | **10.115** | PASS (`verify_lut_U.json`, 0.991, worst_x 816489) |
| invsqrt_lut_U2.kmb | U with `--maxq 109` (kickmix trades ~14 adder ancilla-Toffolis per qubit) | 109 | 1618 | 1880.49 | 204,973.19 | **10.132** | PASS (`verify_lut_U2.json`, 0.991) |
| invsqrt_lut_V.kmb | **own Gidney adder** (`lutpoly11.py --gadd --pad 0`, init_and/del_and, implicit-zero source extension so the 7-qubit zero pad is gone, native carry-in for the rounded rows so the extra `l` bit and its AND are gone; arithmetic identical to U, same model error 2^-24.01). Horner 397→352 Toffoli per direction, peak 109→101 | 101 | 1528 | 1790.49 | 180,839.28 | **11.484** | PASS (`verify_lut_V.json`, 0.991) |
| invsqrt_lut_W.kmb | V + **top-CCX Gidney adder** (`lutpoly13.py --topccx`, same flags as V): the carry into each adder's top target bit is XORed in with one CCX instead of being stored by init_and, so every adder needs n-2 ancillas; same 1528 Toffoli, same arithmetic (exhaustive classical check n<=6) | 100 | 1528 | 1790.49 | 179,048.79 | **11.599** | PASS (`verify_lut_W.json`, 0.991) |
| invsqrt_lut_X.kmb | W + **two-level Horner window** (`lutpoly14.py --topccx --groups 1:7:13`): y-step rows i<7 (sources only 6..12 bits) go into a 13-bit window with its own 2 signed carry qubits (exact range check over all x_norm: [-6510, 15940]), folded once into the 19-bit window; those rows cost 14 instead of 20 Toffoli. -70 Toffoli, +2 q | 102 | 1458 | 1720.49 | 175,489.77 | **11.834** | PASS (`verify_lut_X.json`, 0.991) |
| invsqrt_lut_Y.kmb | X + **mixed Gidney/Cuccaro adders** (`lutpoly15.py --maxanc 13`, `gadd_mix.py`): adders that would need more than 13 ancillas switch their top source positions to in-place MAJ/UMA carries (+1 CCX per position, no ancilla); only the 6 big y-step rows are affected (+6 CCX each per direction, +70 total), peak 102 -> 96 | 96 | 1528 | 1790.49 | 171,886.84 | **12.082** | PASS (`verify_lut_Y.json`, 0.991) |
| invsqrt_lut_Z.kmb | Y + s-aware coefficient search (`lutpoly16.py`) | 96 | 1528 | 1782.61 | 171,130.46 | 12.135 | PASS (`verify_lut_Z.json`, 0.971) |
| invsqrt_lut_AA.kmb | **Z + one carry qubit per Horner window** (`lutpoly18.py --onecarry --groups 1:7:14`): every window one bit wider (same adder length), the lookup loads a per-segment offset k in {0,-1} (window sign bit + hi) so the final window value fits [-2^W, 2^W); folds become `hi -= c`. 3 windows x 1 qubit | 93 | 1522 | 1776.61 | 165,224.63 | **12.569** | PASS (`verify_lut_AA.json`, 0.971) |
| invsqrt_lut_AB.kmb | AA + **y LSB never phased and not in the denorm lane** (`--droprot 1 --droplane --DSH 6`): -4 CSWAP per direction, 34 rotations | 93 | 1514 | 1768.80 | 164,498.06 | 12.625 | PASS (`verify_lut_AB.json`, 0.991) |
| invsqrt_lut_AC.kmb | AB + `--jmin8 1` (shift-by-8 stage leaves lane bit 0 in place) | 93 | 1512 | 1766.80 | 164,312.06 | **12.639** | PASS (`verify_lut_AC.json`, 0.991) |
| invsqrt_lut_AD.kmb | AC + **one prefix AND chain for all four s bits** (`lutpoly21.py`, `binnorm2.py`): s_r = XOR of P_2k = [top 2k bits zero]; normalize 84+80 -> 77+77 Toffoli | 93 | 1502 | 1756.80 | 163,382.06 | **12.711** | PASS (`verify_lut_AD.json`, 0.991) |

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
python3.13 supervisor_work/invsqrt/lutpoly11.py --packflags --rangeq --fy 28 --clamp --binnorm --zshift --droptop --smallfirst --foldadd --guards=0,-2,-4 --round 1,2 --gadd --pad 0 --out V.kmb   # = invsqrt_lut_V.kmb (current best, sha ebc32b19)
python3.13 supervisor_work/invsqrt/lutpoly.py --packflags --rangeq --fy 28 --guards 0,1,1 --out E.kmb   # byte-identical to invsqrt_lut_E.kmb
PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py E.kmb             # ~6 min on 4 cores
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --out H.kmb   # byte-identical to invsqrt_lut_H.kmb
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --out J.kmb   # = invsqrt_lut_J.kmb
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --zshift --out K.kmb   # = invsqrt_lut_K.kmb
python3.13 supervisor_work/invsqrt/lutpoly4.py --packflags --rangeq --fy 29 --guards=0,-1,-4 --pad 6 --clamp --binnorm --zshift --droptop --out L.kmb   # = invsqrt_lut_L.kmb (current best)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --guards=0,-2,-4 --pad 6 --clamp --binnorm --zshift --droptop --droprot 1 --out N.kmb   # = invsqrt_lut_N.kmb (current best, ~25 s)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --guards=0,-2,-4 --pad 6 --clamp --binnorm --zshift --droptop --droprot 1 --smallfirst --foldadd --out Q.kmb   # = invsqrt_lut_Q.kmb (drop --foldadd for P)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 29 --clamp --binnorm --zshift --droptop --droprot 1 --smallfirst --foldadd --guards=0,-3,-5 --round 1,2 --pad 7 --maxq 111 --out T.kmb   # = invsqrt_lut_T.kmb (sha e8f2d083)
python3.13 supervisor_work/invsqrt/lutpoly7.py --packflags --rangeq --fy 28 --clamp --binnorm --zshift --droptop --smallfirst --foldadd --guards=0,-2,-4 --round 1,2 --pad 7 --maxq 110 --out U.kmb   # = invsqrt_lut_U.kmb (sha a71c37df); with --maxq 109 = invsqrt_lut_U2.kmb (current best, sha 27d75c8f)
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

## 2026-11-05 07:xx run
- fy=28 + `--round 1,2` + guards 0,-2,-4, no droprot: model 2^-24.01, verifier worst err/tol 0.991 -> PASS. pad6: 110q/1606 (205,533.67, 10.104x, full PASS);
  pad7+maxq110: 110q/1604 (205,313.67, **10.115x**, full PASS, = U). pad7 alone 111q/1592; pad8/9+maxq110 110q/1604/1606.
- `lutpoly9.py` (search + a0 centring only over reachable x_norm): same 2^-24.01 (worst segment is at s=0 where every x_norm is reachable). No gain.
- maxq sweep at U settings (pad 7): 111/1592, 110/1604, **109/1618 (U2, 10.132x, full PASS)**, 108/1636 (est 10.129x), 107/1658, 105/1708; pad 6 or 8 at maxq 109: 1620.

## Qubit ledger + pad sweep (supervisor, 2026-11-06 23:xx UTC)
- `qubit_ledger.py U2.kmx`: peak live qubits per top-level mark (R = alloc, HMR = free). U2: normalize 37, lookup 86,
  **horner 109**, denormalize/phase 99, lookup_inv 88. The 109 peak is horner only (base 88 = x 22 + sbp 4 + regs 51 +
  pad 7 + carry 4, plus ~21 adder ancillas). Getting below 99 needs the denormalize/phase stage shrunk too.
- Pad sweep (U2 flags, static Toffoli, Q x (T+262)): pad 0 -> 104q/1774 (211.7k); pad 3 -> 107q/1672 (206.9k),
  with maxq 105 -> 105q/1714 (207.5k); pad 5 -> 109q/1624; pad 5 maxq 105 -> 105q/1702. U2 (pad 7, maxq 109) = 204.97k stays best.
- U2 re-verified with salt sv0711: full 200,540,928 shots PASS, 10.132x (`verify_lut_U2_sv0711.json`).

## Non-uniform segments (supervisor, 2026-11-07 00:xx UTC) — closed
- `lutpoly10.py` (+ generated `lutpoly6nu.py`, `lutpoly7nu.py`): M in [2,4) uses double-width segments (h^3 M^-3 error scaling),
  Horner digits = low 14 bits of x_norm for every x, x[13] doubles as address bit for M < 2; lookup = 8-bit unary iteration
  (192 values) + nested 1-bit iteration on x[13] for the 64 values with M < 2.
- U2 flags (`--fy 28 --guards=0,-2,-4 --round 1,2 --pad 7`, no maxq): lookup 383 -> **255** as predicted, but horner 397 -> 468
  per direction (one more row per step, b1 17 -> 18 bits, b2 7 -> 9 bits because in 14-bit digit units the M < 2 coefficients
  double/quadruple), 115 q, 1632 Toffoli, model err 2^-23.78 (fails). Q x (T+262) = 217.8k vs U2 205.0k. **Closed.**
- U2 re-verified with salt sv0700: full 200,540,928 shots PASS, 10.132x (`verify_lut_U2_sv0700.json`).

## Column-drop, deg3, k=8, droprot on V (supervisor, 2026-11-07 02:xx UTC) — all closed
- V rebuilt in a fresh container: byte-identical (sha ebc32b19); official verifier with salt sv0207, full 200,540,928 shots **PASS**, 180,839.28 = 11.484x (`verify_lut_V_sv0207.json`).
- `lutpoly12.py` = lutpoly11 + `--lam j:L` (Horner step j drops every product column below acc bit L, so every row adder is L ANDs shorter
  and the peak adder needs L fewer ancillas; rounding carry-in moves to src bit L-e-1). Model error (V flags, search R=3):
  1:1 -> 2^-23.60, 1:2 -> 2^-22.98, 2:1 -> 2^-23.58; fy28 0,-1,-4 1:1 -> 2^-23.79; 0,-2,-3 1:1 -> 2^-23.71 (all fail);
  fy29 0,-1,-3 1:1 -> 2^-24.91 but 106 q / 1618; fy29 0,-1,-3 1:2 -> 2^-24.07, 105 q / 1592 (194.7k, worse than V 180.8k);
  fy29 0,-2,-4 1:2 -> 2^-23.96; 0,-2,-5 / 0,-3,-5 1:2, 0,-2,-4 1:3, 0,-2,-4 1:2+2:1 all fail. Each dropped column costs ~0.4 bit. **Closed.**
- `deg3_search.py` (deg-3 coefficient search; lutpoly7's search only knew deg 2, that was the IndexError): k=7 fy28 guards 0,-2,-4,-6
  -> widths 28/19/11/3 (+9 coefficient qubits vs deg 2), err 2^-22.5 for every round setting. Paper estimate even with enough guards:
  lookup -290 but horner +~190/dir and +11 q -> worse. **Closed.**
- k=8 (gadd, fy28): 0,-1,-3 round 1,2 -> 107 q / 1512 (189.8k); 0,-1,-4 -> 2^-24.00, 106 q / 1508 (187.6k); 0,-1,-5 fails. Worse than V.
- V + `--droprot 1` FAILS (x=3071203, 3.423e-11 > 3.401e-11), `--droprot 2` FAILS (x=876875). V has no rotation slack.

## Top-CCX adder (supervisor, 2026-11-07 03:xx UTC)
- V rebuilt byte-identical (ebc32b19), verifier salt sv0307 full PASS 11.484x (`verify_lut_V_sv0307.json`).
- `lutpoly13.py --topccx`: lutpoly11 with `gadd` replaced by `gadd_top` (last carry -> CCX straight onto the top target bit, del_and side skipped).
  Exhaustive classical check (n<=6, all m, cin, sub). W = V flags + `--topccx`: 100 q / 1528 Toffoli / 179,048.79 = **11.599x**, full verifier PASS (sha f145f85e).
  `python3.13 supervisor_work/invsqrt/lutpoly13.py --topccx <V flags> --out W.kmb`
- `lutpoly14.py` (+ `group_scan.py`): `--groups j:a:LA` puts Horner rows i<a of step j into a narrow LA-bit window with its own 2 carry qubits, folded once.
- X = W flags + `--groups 1:7:13` (`group_scan.py`: best y-step split a=7/LA=13 saves 42-7 = 35 Toffoli per direction; r-step split saves only 11/dir and its carries would stay live through the y-step peak, so not used):
  102 q / 1458 Toffoli / 175,489.77 = **11.834x**, full verifier PASS (sha eaaa147a). Peaks: horner 102, denorm/phase 94.
  `python3.13 supervisor_work/invsqrt/lutpoly14.py --topccx --groups 1:7:13 <V flags> --out X.kmb`

## Mixed Gidney/Cuccaro adder (supervisor, 2026-11-07 03:xx UTC)
- `gadd_mix.py`: per carry position either Gidney (fresh ancilla, init_and/del_and, top carry by CCX) or Cuccaro MAJ/UMA (carry stored in place
  in the source bit, +1 CCX, no ancilla). Exhaustive classical check n<=7, all m, maxanc in {None,0..3}, cin, sub: 0 failures.
- `lutpoly15.py --maxanc N` (= lutpoly14 with all adders via gadd_mix). X flags: N=99 rebuilds X byte-identical; N=13: 96 q / 1528 (Y, 12.082x, full PASS);
  N=12: 96 q / 1554 (fold fan-out peak); N=11: 96 q / 1580. Group splits with N=13: 6:12 -> 98 q (fold), 8:14 -> 96/1534, 9:15 -> 96/1548. Y stays best.
  Below 96 each qubit costs one extra CCX in all 13 y-step rows x 2 directions (26 > C/Q = 18.7), so not profitable.
  `python3.13 supervisor_work/invsqrt/lutpoly15.py --maxanc 13 --groups 1:7:13 <V flags> --out Y.kmb`   # sha 9c03bbeb

## s-aware coefficient search (supervisor, 2026-11-07 04:xx UTC)
- Y rebuilt in a fresh container: byte-identical (sha 9c03bbeb); verifier salt sv0507 full 200,540,928 shots PASS 12.082x (`verify_lut_Y_sv0507.json`).
- `lutpoly16.py --wsearch` objective (always on): the verifier's rotation budget is min_x (tol(x) - |err(x)|) in absolute turns, which for
  x_norm = x 4^s is proportional to 2^s (2^-24 exact_y - |err_y|); the binding s per x_norm is 0 if x_norm <= MAX_X, 1 if x_norm % 4 == 0, else unreachable.
  Per segment it picks (d1, d2) in [-3,3]^2 and the integer a0 shift (centre +-4) maximising that weighted min slack, then clamps.
  Z = Y flags through lutpoly16: same 96 q / 1528 Toffoli, worst err/tol 0.99075 -> 0.97092, rotation eps 5.48e-14 -> **1.669e-13** (predicted exactly),
  C 1790.49 -> 1782.61, score **171,130.46 = 12.135x**, full verifier PASS (sha 188a2b4d, `verify_lut_Z.json`).
  `python3.13 supervisor_work/invsqrt/lutpoly16.py --packflags --rangeq --fy 28 --clamp --binnorm --zshift --droptop --smallfirst --foldadd --round 1,2 --gadd --pad 0 --maxanc 13 --groups 1:7:13 --guards=0,-2,-4 --out Z.kmb`
- Closed with the new objective (model check): guards 0,-3,-4 / 0,-2,-5 / 0,-3,-5 (weighted slack -8 / -6 / -11 y units); R=5 no change;
  droprot 1 passes but 34 x 29.92 T = 35 x 29.07 T (no gain); droprot 2 fails (1.099); k=8 (0,-1,-4, any group) fails (1.0004) and is 100-102 q / 1524.

## 2026-11-07 05:xx UTC (supervisor)
- Z rebuilt in a fresh container: byte-identical (sha 188a2b4d); verifier salt sv0705z full 200,540,928 shots PASS 12.135x (`verify_lut_Z_sv0705z.json`).
- `lutpoly17.py` (closed): fan-out-free carry folds, `hi += c0 - 2 c1` as `c1 ? ~(~hi + [c0, c1&~c0]) : hi + c0` (+1 AND per fold).
  Removes the fold's len(hi)-1 fan-out qubits, but after that the 96 peak is set by the 6 big y-step rows (13 Gidney ancillas each):
  maxanc 13: 96 q / 1534; 12: 95 / 1560; 11: 94 / 1586 (all worse than Z's 96 / 1528). `fold2_sweep.py` group scan
  (a in 6..10, LA in 11..17, maxanc 11..13) with fold2: best estimate 171,707 (= 7:13), no gain.
- `b2_tree.py` (closed): dropping b2 (7 q) between Horner step 2 and its inverse would lower denorm 94->87 and step-1 96->89,
  but re-loading b2 needs a pruned unary tree: exact b2 needs 159 leaves (84 distinct values), i.e. ~2x158 Toffoli, 89 x 2099 = 186.8k > 171.1k.
  Sharing b2 across segments: spread 2 / 5 / 12 for groups of 2 / 4 / 8, and one b2 unit is 16 y units (~2 y units after a linear refit)
  vs a min weighted slack of 0.51 y units, so sharing is infeasible at fy=28.

## One carry qubit per window (supervisor, 2026-11-07 06:xx UTC) — lut_AA
- Z rebuilt in a fresh container byte-identical (188a2b4d); verifier salt sv0607z full PASS 12.135x (`verify_lut_Z_sv0607z.json`).
- With k=0 the window carry takes 3 values {-1,0,1} (needs 2 qubits) for every W. But the window's start value is just loaded
  data: per segment the table can store window = (a0 mod 2^W) + k 2^W (sign bit = carry qubit, k in {0,-1}) and hi = (a0 >> W) - k.
  Then only the per-segment span of the final value must fit 2^(W+1). Exact check over all x_norm: step 2 W=10, step 1 W=20,
  group window W=14 are feasible for all 384 segments (= old L+1, so adder lengths are unchanged). Nested group window: after
  its fold the outer window value is a0 - S_A - hi0 2^W (independent of kA), so the two offsets are chosen independently.
- `lutpoly14oc.py` (= lutpoly14 + `--onecarry`), `lutpoly18.py` (lutpoly16 on top of it). Without `--onecarry` rebuilds Z byte-identical.
  `python3.13 supervisor_work/invsqrt/lutpoly18.py --packflags --rangeq --fy 28 --clamp --binnorm --zshift --droptop --smallfirst --foldadd --round 1,2 --gadd --pad 0 --maxanc 13 --guards=0,-2,-4 --onecarry --groups 1:7:14 --out AA.kmb`   # sha 9c93deb2
- AA re-verified with salt sv0607aa: full PASS, same score (`verify_lut_AA_sv0607aa.json`).
- AA: 93 q / 1522 Toffoli (folds without fan-out: -6), same arithmetic as Z (worst err/tol 0.97092, eps 1.669e-13), score 165,224.63 = **12.569x**, full verifier PASS.
  Peaks: lookup 89, horner 93, denorm/phase 91.
- Scan with --onecarry: maxanc 12 -> 92/1548 (165.8k), 14 -> 94/1510 (165.9k); groups 1:6:13 93/1536, 1:8:15 93/1528, 1:7:15 93/1548, +2:4:6 94/1530. AA best.

## Freeing window sign qubits after their fold (supervisor, 2026-11-07 07:xx UTC) — closed
- AA rebuilt in a fresh container byte-identical (9c93deb2); verifier salt sv0707aa full PASS 12.569x (`verify_lut_AA_sv0707aa.json`).
- Idea: after `hi -= c`, c = bit0(hi') ^ bit0(hi0(A)); for the group window cA = bit_LA(acc') ^ bit_LA(loaded(A)). If the
  classical bit equals a cheap function p of qubits that hold constant data at that moment, CX gates clear c and the
  qubit is free during the step-1 B rows (horner peak) and denorm/phase: c2 + cA would give 93 -> 91 q at no Toffoli cost.
- `lutpoly19.py` (= lutpoly14oc + `--freecarry` / `--freefeat` / `--wplus`), `lutpoly20.py` (launcher like lutpoly18), `fcrepair.py`.
- Result: infeasible everywhere. k in {0,-1} is forced in 47 (step 2) / 127 (step 1) / 132 (group) of 384 segments, and the
  forced parities are essentially random:
  - affine in the 9 address bits: best leaves 11 / 47 / 47 bad segments; + one AND of two linear forms: 0 solutions;
  - parity-aware re-choice of (d1, d2, a0 shift) among the lutpoly16 candidates with slack >= the current minimum: no assignment;
  - features = address + b2 + loaded y bits (43 features for c2): not solvable;
  - a wider window does not create freedom: k=+1 and k=-1 give the same window bit pattern and the same hi0 parity, so the
    parity is fixed by the pattern; two extra bits per window would be needed (> the 19 Toffoli/qubit break-even).

## Dropping y's LSB from the denorm lane (supervisor, 2026-11-07 21:xx UTC) — lut_AB
- AA rebuilt in a fresh container byte-identical (9c93deb2); verifier salt sv0721aa full PASS 12.569x (`verify_lut_AA_sv0721aa.json`).
- `--droprot 1` only skipped the Z_POW on lane bit 0 (= y bit 0 only when s = 0). New `--droplane` (lutpoly14oc build +
  lutpoly16 search): y bits < droprot are never phased for any s, so they are not put into the denorm lane at all:
  every smallfirst CSWAP stage is one shorter (-4 CSWAP per direction). The coefficient search re-drops the bits after
  each a0 shift (dropping is not shift-invariant; without that the search picked infeasible offsets, err/tol 1.078).
  `python3.13 supervisor_work/invsqrt/lutpoly18.py <AA flags> --droprot 1 --droplane --DSH 6 --out AB.kmb`   # sha 3e3a26d8
- AB: 93 q / 1514 Toffoli / 34 rotations (eps 5.64e-14), C 1768.80, score **164,498.06 = 12.625x**, full verifier PASS
  (`verify_lut_AB.json`, worst err/tol 0.99075). Without the new flags AA is still rebuilt byte-identical.
- Closed: `--droprot 2 --droplane` fails (1.134); R=4 same as R=3. Partial CSWAP shifts in the denorm stages that only fire
  for s >= 2^r (leave lane bits < jmin unshifted): exact phase simulation over all x (`lanesim.py`, input dumped with
  `DUMP_Y=y.npz` from lutpoly16's slack report) shows only the shift-by-8 stage (s >= 8, x <= 63) tolerates jmin=1 without
  lowering the global min slack; the error is relative, so a larger s gives no extra relative room for stages 1/2/4.
- AB salt sv0721ab: full PASS, same score (`verify_lut_AB_sv0721ab.json`).
- **lut_AC** = AB + `--jmin8 1` (that one CSWAP skipped per direction): 93 q / 1512 Toffoli, same eps 5.64e-14,
  score **164,312.06 = 12.639x**, full verifier PASS (`verify_lut_AC.json`; salt sv0721ac also PASS, `verify_lut_AC_sv0721ac.json`), sha 0b220fec (rebuild identical).
  `python3.13 supervisor_work/invsqrt/lutpoly18.py <AA flags> --droprot 1 --droplane --DSH 6 --jmin8 1 --out AC.kmb`
- k=8 re-checked with --onecarry (groups 1:8:15): guards 0,-1,-4 fail (1.0004); 0,-1,-3 pass but 98 q / 1524; fy 29 group
  window infeasible. Closed again: the lookup saves 192 but b1/b2 widen and Horner grows.

## One prefix AND chain for the normalization (supervisor, 2026-11-07 22:xx UTC) — lut_AD
- AC rebuilt in a fresh container byte-identical (0b220fec); verifier salt sv0722ac full PASS 12.639x (`verify_lut_AC_sv0722ac.json`).
- `binnorm.py` built s bit by bit: stage r ANDs the top 2^(r+1) bits of the *already shifted* x (15+7+3+1 = 26 Toffoli forward,
  14+6+2+0 = 22 inverse). But with P_2k = [top 2k bits of the original x are zero] = [s >= k] (the even prefixes of ONE chain
  over the negated bits x21..x2, 19 ANDs) every bit of s is a parity: bit r of s toggles at every multiple of 2^r, so
  s0 = P2^P4^...^P20, s1 = P4^P8^P12^P16^P20, s2 = P8^P16, s3 = P16 (checked classically for all x). `binnorm2.py` computes s
  with CX gates from the chain, erases the chain by measurement (del_and), then does the same four zero-top shifts.
  Inverse: un-shift, recompute the chain, clear s with the same CXs. Normalize 84 -> 77, normalize_inv 80 -> 77 (peak 37 -> 45, irrelevant).
- **lut_AD** = AC flags through `lutpoly21.py` (= lutpoly18 with binnorm2): 93 q / 1502 Toffoli, same arithmetic (worst err/tol 0.99075,
  eps 5.64e-14), score **163,382.06 = 12.711x**, full verifier PASS (`verify_lut_AD.json`; salt sv0722ad also PASS, `verify_lut_AD_sv0722ad.json`), sha 01c10986.
  `python3.13 supervisor_work/invsqrt/lutpoly21.py <AA flags> --droprot 1 --droplane --DSH 6 --jmin8 1 --out AD.kmb`
- Closed (analysis): direction "reload y's high bits": hi0(A) = y >> 20 is a monotone staircase with 128 distinct values over
  the 384 segments (127 steps), so any reload is >= ~127 Toffoli; even if every stage dropped to 86 q, 86 x (1757 + 127 + ~30) =
  164.6k > 163.4k. Normalize CSWAP counts (6/14/18/20) are already tight for the reachable s values.
