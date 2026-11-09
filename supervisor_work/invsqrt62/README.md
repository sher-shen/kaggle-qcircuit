# invsqrt — starting from the public 62-qubit circuit (supervisor, 2026-11-05 22:xx UTC)

Nothing here was submitted to Kaggle. No third-party circuit file is committed; the source op list is
`tools/circuit-viewer/ops.json` of the public Apache-2.0 repo `manwithacat/kickmix-macos`
(`git clone --depth 1 https://github.com/manwithacat/kickmix-macos`; the cloud git proxy serves it).

## Reproduce the public frontier circuit in the cloud
```
python3 -I supervisor_work/invsqrt62/ops2kmx.py <kickmix-macos>/tools/circuit-viewer/ops.json p62.kmx
PYTHONPATH=data/kickmix python3.13 -c "import kickmix as km; km.Circuit.from_file('p62.kmx',format='kmx').to_file('p62.kmb',format='kmb')"
# p62.kmb sha256 = 67482db6c53896348eadba126924868ed3011d7e1576a6d0abb6f7c137ae4997 (byte-identical to the public file)
PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py p62.kmb   # ~10 min on 4 cores
```
Official verifier, full 200,540,928 shots, default salt: **PASS, Q 62, Toffoli 1327.48 (mean), C 1624.07, score 100,692.58 = 20.625x**
(`verify_public62.json`). Rotations: 41 per shot, eps 2.43e-13 -> 41 x 28.8 T = 295 Toffoli-eq (18% of C).
Note: ops.json Z_POW angles are in turns (numerator / 2^128 in `zpow_exact`); kickmix Z_POW takes half-turns.

## Analysis tools (all run on ops.json, no kickmix needed)
- `phase_trace.py ops.json out.npz`: exact basis-state trace over all 3,133,452 x (~4 min): phase error vs the
  verifier's target, tol, which rotation fired per x, executed Toffolis. Reproduces the verifier exactly
  (worst ratio 0.99932377 at x=161, mean Toffoli 1327.48). Absolute min margin 5.86e7 (2^-64 turns) at x=52229.
- `angle_lp.py trace.npz deltas.npy`: cutting-plane LP re-fitting the 41 free rotation angles to maximise the
  min margin (which sets eps). **Result: no gain (x1.0000000)** — the published angles are already minimax-optimal.
  Upper bound of this direction anyway: margin <= min tol (~10x) -> at most ~20 Toffoli-eq (1.2%).
- `peephole_scan.py ops.json [N]`: Toffoli-class gates with constant / equal / complementary controls on every
  execution. **Result: none that run on more than 1.6% of inputs** (only rare measurement-conditioned CCZs; < 0.1 Toffoli total).
- `pair_scan.py ops.json`: static scan for two ANDs into one target sharing a control (yoyobar's 3->2 AND trick)
  with nothing in between. **Result: 0 pairs left.**

## Width analysis (2026-11-05 23:xx UTC): can the public circuit drop to 61 qubits?
- `live_trace.py ops.json live.npz [stride]`: exact liveness over **all** x (~50 s). A qubit that is 0 for every x
  is genuinely |0> (no Hadamards outside HMR). Result: **peak 62 on 15,720 ops**, first/last at op 3823 / 36834.
- `windows.py stages.json live_occ.npy wins.npy`: the 62-wide stretches, merged (gaps <= 3 ops) and split by stage:
  coeff_lookup 1 window (10,578 ops), early_phase_taps 4 (627), front_decoder_compute 7 (2,090), arith_b 16 (88),
  fine_phase_stream 7 (224), arith_c 17 (156), lookup_c 2 (1,773), late_curvature_norm 13 (218) — **67 windows**.
- `rank_win.py ops.json wins.npy`: affine GF(2) rank of the live wires at the start/middle/end of each window
  (10k x sample, incl. all x <= 4096). 176 of 200 probes are **full rank**: only late_curvature_norm (deficit 7..14)
  and 3 tiny windows (ops 16630, 24269, 24746; deficit 1) could be freed with CNOTs alone.
- So 61 qubits needs non-linear re-synthesis of coeff_lookup, the front decoder, lookup_c and ~33 adder carry
  windows. Break-even budget for one wire is ~26 Toffoli-eq (1/62 of C); the 63->62 step already cost 5 ANDs in
  coeff_lookup alone. Not attempted further.

## Linear-AND scan (2026-11-05 23:xx UTC): any Toffoli whose product is affine in the live wires?
- `linear_and_scan.py` (one shot per x) reported 55 "hits" (12 gates executed on >= 5% of shots, ~2.1 Toffoli mean,
  mostly measurement-conditioned CCZ in phase_merge_repair and unnormalize whose product looked always 0).
- `linearize.py` replaced those 12 by Clifford gates -> **official verifier FAIL** (x=3, phase error 0.5).
  Cause: wire values depend on the HMR outcome history (classically controlled CX fix-ups), and one shot per x
  sees only one history. Re-run with every x repeated 32 times (`linearize.py ... 0.05 3000 "" 32`): **0 gates**.
  With minfrac 0 it only finds 40 gates that are essentially never executed (artefacts). **Direction closed.**
- Lesson: any sampling search on this circuit must repeat each x over many outcome draws (the verifier uses 64).

## Rotation drop scan + conditional-block stats (2026-11-06 00:xx UTC, supervisor)
- Re-ran `phase_trace.py` in a fresh container: identical (worst ratio 0.99932377 at x=161, min margin 58,597,850 at
  x=52229, mean Toffoli 1327.48). Note: the verifier counts **all 41** rotation ops per shot (unconditioned Z_POW),
  although on average only 13.8 have their qubit = 1.
- `drop_rot.py trace.npz [ks]`: fix one rotation to the nearest multiple of 1/8 turn (usually 0 = delete) and LP re-fit the
  other 40 angles. Tested the smallest group-2 angles (rot 15..18, 1.4e-11..1.2e-10 turn), rot 0 (3.8e-6 turn) and the
  rarely-firing high rotations (13, 14, 40: fire only for x <= 1023 / 255 / 252). **All INFEASIBLE** (best margin
  -1.1e9 units for rot 15, much worse for the rest). Deleting a rotation is not possible; direction closed.
- `cond_stats.py ops.json 3000 16` (each x repeated 16 times, ~2 s): 142 outermost PUSH_CONDITION blocks hold only
  **51.5 of the 1327.5 mean Toffolis**, all with p ~ 0.5 (measurement-based uncompute fix-ups). The typical block
  (e.g. ops 29805-29831) is AND + CCZ = 2 Toffolis evaluating a degree-4 phase polynomial, which needs >= 2 non-Clifford
  gates, so it is locally optimal. The two big ones (46862-46981 and 46982-47211, ~10 static each, p 0.5) are the only
  ones worth a closer look (<= ~5 Toffoli mean, 0.4%).

## Commutation-aware AND pairs + CSWAP target scan (2026-11-06 01:xx UTC, supervisor)
- Re-built `p62.kmb` from ops.json in a fresh container: sha 67482db6... byte-identical again.
- `comm_pair_scan.py ops.json 1500`: generalises `pair_scan.py` with a per-qubit role model (Z = control/diagonal,
  X = X-type target, O = other); a pair may be brought together if everything between commutes with one of them
  (incl. CX onto the shared target, ops inside nested condition blocks, condition bit not rewritten).
  Patterns CCX a b t/CCX a c t, CCZ sharing 2 qubits, identical CCX pairs. Checked on a synthetic case (finds it).
  **Result on the public circuit: 0 pairs** (window 1500 ops, no early stop). Direction closed.
- `peephole_scan2.py` (peephole_scan + CSWAP targets complementary when control=1 -> 2 CX; one target 0 is info only):
  **0 complementary CSWAPs**. 9 CSWAPs in unnormalize (46766, 46793-46800) and 29531 always have one target 0 when
  the control is 1, which does not save a Toffoli. A one-seed hit "47040 CCZ control const 0 (p 0.124)" disappears with
  another seed (sampling artefact, same lesson as the linear-AND scan).
- Verifier detail relevant to future work: `n_rot` is the *mean executed* count of non-Clifford rotations
  (`num_z_pow(min_clifford_hierarchy_level=4)` / shots), so a rotation inside a measurement-conditioned block only
  costs its execution probability. All 41 rotations here are unconditioned.

## 62q vs 63q stage diff: where the extra Toffolis of the 62-wide build sit (2026-11-06 02:xx UTC, supervisor)
- `segtof.py <viewer> <stage>` counts static Toffoli-class gates between consecutive Z_POWs, 62q vs busyaprime's 63q
  `9a8627`. early_phase_taps differs at the 2^-10 and 2^-6 rotation segments (+1 each) and in the tail; fine_phase_stream
  in the first segment (40 vs 37) and the 2^-17 segment (+1).
- `patch_ops.py in.json edits.json out.json`: range-replacement edits on ops.json with zpow_exact re-keying.
  `qcheck.py out.json 20000 1 2`: sampled exact check (phase, final cleanliness, mean Toffoli), ~2.5 s.
- **Try 1 (early_phase_taps op 15528, CCX 32 16 1)**: the 63q build erases the gated quadratic of the last coarse step by
  HMR + conditioned CZ (0 Toffoli); the 62q build uses a Toffoli. Rewrote it as CX-chain + HMR q1 + conditioned CZ ->
  **FAIL** (qcheck: 27% dirty). Probe: q1 is non-zero on 12.3% of inputs after op 15559 and is consumed at op 16161
  (`CX 21 1`, `CZ 23 1`): the 62q design keeps q1 alive as a rolling register instead of a fresh wire, so the Toffoli
  is the price of the saved wire. Closed.
- **Try 2 (fine_phase_stream op 25874-25875)**: 62q computes `q50 = q23*a ^ q21*b` with 2 Toffolis where 63q uses 1 plus
  an AND stored earlier on the 63rd wire. q21/q23 are mutually exclusive (q21&q23 = 0, q21 0.3 %, q23 20 %) but not
  complementary, so `s1*a ^ s2*b` still needs 2 ANDs without the stored product. Closed unless a wire is freed.

## Per-stage width vs Toffoli, 62q vs 63q (2026-11-06 03:xx UTC, supervisor)
`live_trace.py` occupancy per stage (all x) next to the stage mean Toffoli of the 62q build and of 63q `9a8627`:

| stage | max occ | ops at 62 | Tof 62q | Tof 63q |
|---|---|---|---|---|
| coeff_lookup | 62 | 10,578 | 177.0 | 172.0 |
| early_phase_taps | 62 | 614 | 80.0 | 76.0 |
| front_decoder_compute | 62 | 2,090 | 33.0 | 33.0 |
| arith_a | **61** | 0 | 68.0 | 87.0 |
| lookup_b | **56** | 0 | 43.0 | 43.0 |
| arith_b | 62 | 86 | 198.0 | 197.0 |
| fine_phase_stream | 62 | 210 | 133.0 | 129.0 |
| phase_merge_repair | **60** | 0 | 6.0 | 6.0 |
| arith_c | 62 | 154 | 248.3 | 246.3 |
| lookup_c | 62 | 1,773 | 62.0 | 62.0 |
| late_curvature_norm | 62 | 215 | 134.0 | 134.0 |
| unnormalize | **36** | 0 | 67.14 | 66.53 |

- Every stage where 63q is cheaper is already 62 wide in the 62q build, except `unnormalize`, which has 26 spare wires but
  only differs by 0.6 Toffoli (0.04 %). `segpat.py` shows the differing decoder at ops 46752-46776 maps the 5 bits
  (q0..q3, q23) to the CSWAP-ladder flags (29 patterns); a hand re-synthesis is possible but caps out at 0.6 Toffoli.
- The arith_c difference (2.0) is spread over ~50 re-ordered blocks of the op diff, and the static counts balance out.
  There's no single place to transplant.
- The last two complementary condition blocks (46862-46981 under bit 318 and 46982-47211 under its inverse 8045) share a
  6-AND carry chain. Exactly one branch runs per shot, so hoisting that chain saves nothing. **Closed.**

## unnormalize decoder: provably minimal; 63q stage transplant blocked (2026-11-06 04:xx UTC, supervisor)
- `segmap.py ops.json 46753 46777 0,1,2,3,23,14,15,16,17,18,60 <same> 13000 20000 4`: exact truth table of the decoder
  (deterministic, 29 reachable inputs). With a=q0, b=q1, c=q2, d=q3, f=q23, G=f(a|b): outputs q14=fb, q15=fa~c, q16=fac,
  q17=G, q60=Gd, q23=f^G^q60, q0..q3 = swap(b,a,d,c) masked by ~G; extra phase = bit13000 & f & ~(a|b).
- Rank check: over the 29 reachable inputs, {fa, fb, fac, fab, Gd} are 5-dimensional modulo affine functions, and each
  Toffoli/CSWAP adds at most one new product, so this output contract needs **>= 5 Toffolis**. The 62q decoder uses exactly 5.
- `stage_match.py 46744 45095 ops62.json ops63.json` (+ `simto.py`): at the start of unnormalize, 22 of the live wires map
  1:1 onto 63q `9a8627`, but 62q's q0,q2,q3,q23 (4 wires) and 63q's q0,q2,q3,q23,q56 (5 wires) are **not affine-related**.
  This is the shift-count compression that saved the 62nd wire. Re-expanding it costs Toffolis, so the 63q stage
  (3 ANDs in its decoder, 0.6 cheaper in total) can't be transplanted for free. **Direction closed.**

## coeff_lookup (177 AND) structure and bounds (2026-11-06 05:xx UTC, supervisor)
Run from a scratch dir that has a `w/` subdir (the scripts read and write `w/cl.npz` and `w/F.npy`):
`lut_tt.py ops.json 238 15214 w/cl.npz` (wire states at stage start/end, ~2 s) -> `lut_outputs.py w/cl.npz w/F.npy`
(truth tables over the 8-bit address q14..q21) -> `lut_anf.py`, `lut_split_rank.py`, `lut_andlist.py`, `lut_spanchk.py`.
- The stage computes **35 output wires** (22, 24, 29..61). Each one is an exact function of the address (all 256 covered), and the stage
  phase is a function of the address too. ANF: every output has degree 7-8 and 103-145 monomials. All 247 non-affine
  monomials show up, and the outputs have rank 35 modulo affine functions. So they look like random functions, except
  q60/q41/q44/q43/q57/q40/q59 (3..35 transitions over the sorted address), which are step-like high coefficient bits.
- **The bilinear 4+4 split doesn't help**: for f_k = sum_j m_j(hi) g_kj(lo), the sum of row ranks is **225 for all 35 splits**,
  i.e. 22+225 = 247 ANDs, much worse than 177. The public circuit is not a monomial scheme: `lut_andlist.py` shows
  that 170 of its 177 ANDs multiply two degree-7/8 functions, so it is a general multiplicative-complexity (XAG) circuit.
- `lut_spanchk.py`: no CCX product is in the affine span of the wires that are live at that point (exact over 256 addresses).
  **0 hits**, so no AND can be swapped for CNOTs in place.
- Counting bound (non-constructive): XAG circuits with r ANDs and 35 outputs number about 2^(r^2+53r+315), against 2^8960
  tables, so r >= ~70-85. There may be room below 172, but only a real MC search (SAT/XAG resynthesis) could reach it.
- `lut_flip.c` + `lut_mk_tensor.py`: a GF(2) flip-graph tensor-rank walk. **It doesn't work here**: started from the trivial
  225-term decomposition, it can't even recover a planted rank-60 15x15x35 tensor in 60 s. Do not use it as-is.

## coeff_lookup as XAG + table slack (2026-11-06 06:xx UTC, supervisor)
- Re-built `p62.kmb` (sha 67482db6..., byte-identical) and re-ran the **official verifier, full 200,540,928 shots: PASS**,
  Toffoli 1327.483, C 1624.07, score 100,692.58 (`verify_public62_0606.json`).
- `lut_extract_xag.py ops.json 238 15214 cl.v`: exports the stage as an 8-input / 35-output XAG in Verilog (177 ANDs, no
  conditional blocks inside, the 15 live payload wires q0..q13,q23 are never touched). Ready to feed an external MC
  optimiser (mockturtle `cut_rewriting` + `future::xag_minmc_resynthesis`). **Compiling mockturtle in the cloud session was
  blocked by the permission classifier (external code)**, so this was not run.
- `lut_xag_rank.py cl.v`: none of the 177 AND products is in the GF(2) span of 1, the inputs and the earlier products
  (XAG-level redundancy 0).
- `lut_dcare.py ops.json 30000 5 2 out.npz`: flips each output wire right after the stage, with the first later HMR of every
  output wire forced to outcome 0 (= a perfectly consistent phase fix-up), and records the worst error per address.
  The fix-ups of the measured-out coefficient wires are Z-only one-hot lookups, so their Toffoli cost doesn't depend on
  the table, and don't-cares would be usable. **But there is no slack**: the 5 early-tap wires (40, 41, 50, 51, 57) give
  >= 6.6e4 x tolerance on every address, and the other 30 make the state dirty (the coefficient feeds in-place arithmetic
  that is uncomputed later). A table don't-care search on single bits is **closed**. A cheaper table would have to change
  the arithmetic contract too.

## coeff_lookup MFFC check + AND-recomputable wire scan (2026-11-06 07:xx UTC, supervisor)
- Re-built `p62.kmb` again (sha 67482db6..., identical). Re-ran the official verifier on our own `invsqrt_lut_U2.kmb`
  with a new salt `sv0706` (full 200,540,928 shots): **PASS, score 204,973.19 = 10.132x** (`../invsqrt/verify_lut_U2_sv0706.json`).
- `xag_affine.py cl.v xag.json` converts the exported XAG into affine form (every signal = const ^ XOR of inputs and AND
  outputs). `xag_mffc.py xag.json` does the AND-level fanout and MFFC analysis. **Every one of the 177 ANDs has an MFFC of size 1**
  (fanout 1..137, most ANDs feed dozens of later ANDs as linear terms). Cut rewriting (mockturtle `cut_rewriting` +
  `xag_minmc_resynthesis` included) gains `|MFFC| - new ANDs`, so a single pass can only win if a node's function is in
  the affine span of existing nodes. `lut_xag_rank.py` already showed that never happens. **Local MC re-synthesis (instructions 1/2
  of the 06:45 report) is closed: expected gain 0 without zero-gain restructuring or a global SAT/exact MC search.**
- `andfree_scan.py ops.json wins.npy 2000 3`: at the start and middle of all 67 62-wide windows (each x repeated 3 times), looks for a live
  wire w = (a&b) ^ affine(other live wires). Such a wire could be measured out for free and recomputed later with 1 Toffoli, freeing a line.
  **coeff_lookup (the 10,578-op window): 0 such wires**, and also 0 in front_decoder_compute. They show up only in
  short (4..40-op) arith_b/arith_c/fine_phase_stream carry windows. So 61q costs much more than 1 Toffoli per
  window, and freeing a line just for fine_phase_stream does not lower Q.
- 63q's cheaper 2^-17 tap (63q ops 27162-27168) uses q48 as a **long-lived rolling register** (holds q21*q54 ^ ... from
  earlier in the stream, 19% non-zero), not a transient scratch wire. 62q is 62 wide at ops 25860-25880, so the trick can't be
  transplanted (consistent with try 2 above). Closed.

## coeff_lookup output re-encoding check (2026-11-06 21:xx UTC, supervisor)
Run on `F.npy` from `lut_outputs.py` (35 x 256 truth tables, address q14 = LSB .. q21; the two 128-halves are separate regimes).
- `lut_counter_chain.py F.npy`: toggle sets per half. Two **exact binary-counter chains** stand out (each wire toggles only where
  the next-lower one does, and half as often): **A = q41,q57,q40,q51,q50** (MSB->LSB; 3/6/13/26/52 toggles in half 0) and
  **B = q60,q44,q43,q59,q24,q42** (1/3/7/14/28/57). These are the 7 "step-like" outputs from the 05:35 report plus 4 more.
- `lut_counter_fit.py F.npy`: decoded as signed integers mod 2^5 / 2^6 they are smooth decreasing sequences that wrap around.
  B in half 0 = round(cubic(a)) (max residual 0.65), so these wires are the **low n bits of smooth polynomial coefficients**,
  which the downstream arithmetic uses modulo 2^n.
- `lut_counter_extend.py F.npy`: greedy search for a 7th/8th counter bit among the other 24 outputs, also allowing XOR with up to
  2 address/counter bits (free CNOT re-encoding). **No candidate is clearly smoother than a random bit** (best 696 vs 742 random for
  A, 747 vs 841 for B, then gains fade), so the other 24 outputs are not lower bits of A/B under any cheap affine re-encoding.
- Consequence for "change the coefficient contract": only 11 of 35 outputs are smooth. Producing them arithmetically
  (round(p(a)) mod 2^n needs constant-multiply adders, ~15-40 Toffolis) costs more than their amortised share of the 177-AND
  table. The 24 random-looking bits carry the precision and have no single-bit slack (06:45 check). **Offline re-encoding gain: none
  found.** Remaining route is global exact MC synthesis (SAT) of the 24-bit block, not re-encoding.

## coeff_lookup split-by-MSB + SAT exact-MC scaling (2026-11-06 22:xx UTC, supervisor)
- Re-built `invsqrt_lut_U2.kmb` from `lutpoly7.py` (sha 27d75c8f..., byte-identical) and re-ran the official verifier with salt
  `sv0611` (full 200,540,928 shots): **PASS, 204,973.19 = 10.132x** (`../invsqrt/verify_lut_U2_sv0611.json`).
- `lut_split7.py xag.json F.npy` (xag.json from `xag_affine.py`; also writes the 35x256 truth tables): the 35 outputs use
  **all 247** degree>=2 monomials of the 8 address bits. Split on the MSB (q21): f = g(x') ^ x7*h(x'), rank g = rank h = 35,
  g uses all 120 and h all 127 7-var monomials. 120 + 35 = **155 ANDs only if the 35 h_k are held in 35 extra scratch wires**
  (Q 62 -> ~97, cost x1.5). Inside the 4-wire scratch budget a monomial DFS needs 247, and the "compute h into the outputs,
  multiply by x7, MBU + phase-fixup DFS" variant needs ~275. **Split-table direction closed (worse than 177 at width 62).**
- `lut_profile.py F.npy`: toggle counts and ANF degree per output. Even the simplest output (row 33, 1+2 toggles, a threshold
  function) has ANF degree 8.
- `lut_mcsat.py F.npy ROWS r TL`: exact XAG multiplicative-complexity SAT encoding (affine operands over inputs and earlier ANDs,
  CaDiCaL via python-sat). See the SUPERVISOR.md of this run for the timings.
  Single output row 33 (threshold, degree 8, so MC >= 7 and a 7-AND comparator exists): r=6 (36.5k vars) and r=7 (46k vars)
  **both hit the 200 s limit without an answer**. Exact SAT MC does not even reach one 7-AND output, so a 24-output ~150-AND
  block is far out of reach. **SAT exact-MC direction closed** (it would need a heavy external tool like mockturtle's
  exact XAG synthesis with cut enumeration, which is blocked in the cloud session).
- U2 maxq re-check: maxq 108 -> 1636 static Toffoli, maxq 104 -> 1734 (109 -> 1618). Q x C does not improve below 109.

## unnormalize already uses per-stage flag measurement (2026-11-08 03:xx UTC, supervisor)
- Dumped ops 46744-47248: 57 unconditioned Toffoli-class gates (5-AND decoder + 52 CSWAP ladder, one CSWAP already replaced by Özer's patch),
  then the shift flags are X-measured one by one (HMR q19 -> bit 318, q16 -> 319, q14 -> 320, q15 -> 322, q18 -> 321) with nested
  PUSH_CONDITION blocks holding the AND-chain / CCZ phase fix-ups (44 static, ~10 mean). This is the same trick as our lut_AF
  normalize_inv (expected 11). **Porting AE/AF measurement-erasure to the 62q circuit (instruction 1 of 02:40) brings nothing: already there.**

## First improvement over the public 62q circuit: merging Toffoli pairs (2026-11-08 04:xx UTC, supervisor)
- `xag_window_rank.py xag.json` / `xag_qform.py` / `xag_window_and1.py` / `xag_window_and2.py` (coeff_lookup, old instruction 1):
  all 186 truth tables (const, 8 inputs, 177 ANDs) are GF(2)-independent, so a window of k ANDs can only be re-synthesised with k-1
  if the consumers see a <= k-1 dim projection. 230 windows are rank-1 (several CCX into one wire), but (a) formal symplectic rank is
  always full and (b) no single AND(g,h) with g,h in span(const, window operands) or affine/AND x affine candidates matches the sum
  mod earlier signals (sanity: k=1 finds all 177 trivially). **coeff_lookup window re-synthesis closed.**
- `stage_xag.py ops.json A B out.json` (symbolic AND-level affine form of any op range; formal variables = wires at op A; CSWAP,
  classically controlled ops, HMR handled) + `stage_qform.py out.json K [SPAN]` (all windows of <= K ANDs, consecutive or inside a span
  of SPAN ANDs: rank of the consumer projection, best basis by symplectic rank -> minimal formal product count). Run on every stage.
  Minimal hits: arith_a (ops 21455, 21459, 21473), fine_phase_stream (25505, 25509, 25523), fine (25604, 25607), arith_c (28843, 28846).
- The last two are artefacts: they are dirty-ancilla CCCX blocks (the same product XORed twice into a non-clean wire, `dirty_pairs.py`
  finds 12 such pairs in the whole circuit, all at width 62, so no clean wire exists to shortcut them).
- The first two are the same real building block: `q_t ^= x*n` then `q_t ^= y*(n+q9+x+q8)` (two CCX into one target, with the shared
  control re-encoded by CNOTs in between) and later a third AND `a = y*(q8+q9)`. Since only the sum reaches the rest of the circuit,
  `x n + y(n + q9 + x + q8) = (x+n)(y+n) + n + a`, so the two CCX become **one CCX on (x+n),(y+n)**, a CX from n, and a CX copying `a`
  from the wire that holds it right after it is computed (the target is idle in between: q19 until op 21584, q40 until op 25536).
  Wire contents after the block are identical, so the circuit is the same permutation + phases on every basis state.
  Edits: `edits/arith_a_merge1.json` (arith_a only) and `edits/merge2.json` (both).
```
python3 -I supervisor_work/invsqrt62/patch_ops.py <kickmix-macos>/tools/circuit-viewer/ops.json supervisor_work/invsqrt62/edits/merge2.json p62mm.json
python3 -I supervisor_work/invsqrt62/ops2kmx.py p62mm.json p62mm.kmx
PYTHONPATH=data/kickmix python3.13 -c "import kickmix as km; km.Circuit.from_file('p62mm.kmx',format='kmx').to_file('p62mm.kmb',format='kmb')"
# merge1 -> sha acd2304a..., merge2 -> sha fc153f1f...
```
- **merge1: official verifier full 200,540,928 shots PASS, Q 62, Toffoli 1326.48, C 1623.07, score 100,630.56 = 20.638x** (`verify_p62_merge1.json`).
- merge2: exact phase trace (`phase_trace.py`) mean Toffoli 1325.48, worst ratio 0.99932377 at x=161 (unchanged).
- **merge2: official verifier full 200,540,928 shots PASS, Q 62, Toffoli 1325.48, C 1622.07, score 100,568.56 = 20.650x**
  (`verify_p62_merge2.json`, worst 0.99932377 at x=161, sha fc153f1f). Nothing was submitted to Kaggle.
- Other checks this run: `uncompute_scan.py` (formal) finds **0** CCX in the whole circuit whose target is affine afterwards (all uncomputes
  are already measurement-based); `dirty_pairs.py`: the 12 dirty-ancilla compute/uncompute pairs all sit at width 62.
- merge2 with salt sv0804mm: full PASS, 100,568.57 (`verify_p62_merge2_sv0804mm.json`).
- Span-40 triple scan (`stage_qform.py st.json 3 40`) adds a periodic series in fine_phase_stream (25707/25749/25752, ...). These are
  **artefacts**: the identity needs a49 again at op 25749, but its wire q50 was HMR-measured at 25715. TODO: restrict factors to the span
  of live wire masks at the window's op. Width-62 dirty chains (25583, 28822): live wires + const are full rank (`lut_tt.py` sample), so a
  wire can't be freed with CNOTs.

## 2026-11-08 05:xx UTC (supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0805mm: PASS,
  score 100,568.535 = 20.650x** (`verify_p62_merge2_sv0805mm.json`).
- Span-40 triple scan (`stage_qform.py st.json 3 40`) finished for arith_b, arith_c, late_curvature_norm, early_phase_taps,
  lookup_c, unnormalize: only arith_c 28843 (known dirty-CCCX artefact) and early_phase_taps hits.
- `stage_qform_plus.py st.json 2 SPAN` ("one AND away": a 2-AND window whose XOR sum + some other AND of the stage is a single
  product) — finds both merge2 edits (sanity). New hits only in the two phase-tap streams (early 15288/15290 + 15364, ..., fine
  25749/25752 + 25707, ...): every tap computes `q_tap = c1*u + c2*v` into a fresh wire that is rotated and HMR'd at once, and the
  shared AND lives in a *different* tap. Using it needs that AND held on an extra wire between the taps; occupancy there is 61..62
  (the 61 is just the tap wire itself), and a dirty copy costs 2 Toffolis (compute + uncompute) = no gain. **Closed.**
- `func_pair_scan.py ops.json 2000 8 80` (sampled/functional, x repeated 8x, recent measurement bits allowed in the remainder,
  remainder may become available on a live wire up to 400 ops later): 125 same-target CCX pairs in the whole circuit, **hits = the
  2 merge2 pairs only**. Nonlinear relations between wires do not open further pair merges.

## General affine factors, tap pairs, wire freeing, triples (2026-11-08 06:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0806mm: PASS,
  score 100,568.51 = 20.650x** (`verify_p62_merge2_sv0806mm.json`). Nothing was submitted to Kaggle.
- `quad_rel_scan.py ops.json 15000 1`: the reachable states DO satisfy many quadratic relations at every same-target CCX pair
  (15..711 independent degree-2 relations among the 52..61 live wires; e.g. live AND outputs). So the formal symplectic rank of
  stage_qform is only an upper bound, and a functional test with arbitrary affine factors is needed (next item).
- `func_affine_scan.py ops.json n reps maxgap EXTRA [A B]`: exact sampled criterion for f = p_i + p_j = g*h + r with g, h, r
  affine in V = live wires at j and at the next read of t + recent measurement bits:  f|{g=0} in V|{g=0} and f|{g=1} in V|{g=1}.
  g = span(4 control values) XOR up to EXTRA further live wires. Sanity on the original ops.json (EXTRA 0): finds exactly the
  two merge2 pairs. On merge2: EXTRA 1 -> **0 of 72 pairs**; EXTRA 2 (~23k-28k g per pair, run in 5 shards) -> **0 of 72 pairs**. **Instruction 1 (pairs) closed for g of weight <= 2 beyond the controls.**
- `tap_pair_scan.py ops.json A B wire n reps DMAX EXTRA` (instruction 2): for every pair of phase-tap values (Z_POW on the tap wire,
  distance <= 4 taps) tests v_i + v_j = g*h + r (g = any live wire or XOR of two, V = live at both taps + bits).
  early_phase_taps (wire 28, 16 taps, 54 pairs) and fine_phase_stream (wire 50, 21 taps, 74 pairs): **0 hits** -> computing tap j
  from tap i on the same wire cannot use fewer than 2 + 2 ANDs (for such g). Note also that the early stream's CSWAP(20,28,3) /
  CSWAP(27,28,0) is a delay line (shift-dependent angle), so tap order is fixed anyway. **Instruction 2 closed.**
- `wire_free_scan.py ops.json P Q n reps EXTRA` (instruction 3): every live wire untouched in the dirty block [P,Q) tested for
  w = g*h + r (other live wires + bits, at P and at Q). Dirty chains 25601-25622 and 28840-28861: **0 of 51 wires** (EXTRA 2).
  The width profile (`occ` sample) has 4-5 free wires only at ~25557-25571, but the chain inputs 40/21/41 are computed after that;
  wire 41 (= erased21 * 47, degree 3) would cost >= 2 Toffoli to recompute plus a non-Clifford fix-up. **Instruction 3 closed.**
- `triple_func_scan.py ops.json n reps maxgap` (3 -> 2): quadrant criterion f|{g1=b,g2=c} in V for g1, g2 = XOR of <= 2 of the six
  control values. Sanity (synthetic: two copies of a CCX inserted after the merge2 pair): both triples HIT. On merge2: **0 of 39 triples**.

## Support-directed affine factors (2026-11-08 07:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0807mm: PASS,
  score 100,568.57 = 20.650x** (`verify_p62_merge2_sv0807mm.json`). Nothing was submitted to Kaggle.
- `support_g_scan.py ops.json n reps maxgap L MAXD [A B]` (instruction 1 of 06:50): for each same-target CCX pair, formal window
  [i-L, j] (wire values at i-L + AND outputs; measurement-conditioned ops give fresh variables, dropped); supp = variables of the
  4 control masks plus the 4 control values themselves; G = V cap span(1, supp) by exact linear algebra on the samples; every g in G
  (if dim G <= MAXD, else 2^MAXD random g) is tested with the func_affine_scan criterion. Sanity on the original ops.json: finds the
  arith_a merge2 pair (L 30 and L 400). Bug caught during sanity: V must be copied at op j (numpy views of q mutate later).
- Result on merge2, L 400, MAXD 13: **0 of 71 pairs** (22 pairs exhaustive with dim G <= 13; the other 49 have dim G 14..28 and
  were sampled with 8192 g each). L 60, MAXD 15: **0 of 71 pairs** (18 exhaustive with dim G <= 15, 53 sampled with 32768 g each; 1.73M g tested).
- Notes: the phase_merge_repair CCZ ladders (4 x 19 CCZ on (18|27, 23|21, *)) are already pivot-search reductions (nested
  "all previous bits zero" conditions -> exactly one CCZ executes), and the seed_phase_retire_2 CCX pairs likewise; no gain there.

## Linear relaxation of the affine-factor test (2026-11-08 21:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0821mm: PASS,
  score 100,568.55 = 20.650x** (`verify_p62_merge2_sv0821mm.json`, worst 0.99932 at x=161). Nothing was submitted to Kaggle.
- `lin_filter_scan.py ops.json n reps maxgap L MAXD` (same arguments as support_g_scan; MAXD unused): tests the *necessary* condition
  f in span(V, G_k*V for all basis vectors G_k of G) with one exact packed GF(2) elimination per pair. A rejection would close
  every g in G at once, whatever dim G is. Run with n 6000, reps 2 (N = 14,030 samples > rows <= 3,567, so a rejection is meaningful).
- Result: original ops.json 71 of 73 pairs **not rejected**, merge2 69 of 71 **not rejected** (only the dirty 25604/28843 pairs
  are rejected, which were already known artefacts). Reason: for these chains the four control values are still live at j, so
  c1, c2, c3, c4 are in G and f = c1*c2 + c3*c4 is in G*V trivially. The relaxation drops the rank-1 condition (h_k = c_k h), and
  that condition is the whole question. So this relaxation cannot replace the per-g search. The 49 pairs with dim G 14..28 stay
  sampled, not exhaustive. An exact method would need a rank-1 completion search over the kernel of (r, h_1..h_d) -> r + sum G_k h_k.
  That kernel includes all the trivial symmetric relations G_k*G_l = G_l*G_k, roughly d^2/2 of them, so it is not cheap.

## Exact pair test by MinRank (2026-11-08 22:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0822mm: PASS,
  score 100,568.51 = 20.650x** (`verify_p62_merge2_sv0822mm.json`, worst 0.99932 at x=161). Nothing was submitted to Kaggle.
- `minrank_core.py` + `minrank_pair_scan.py ops.json n reps maxgap 0 [A B]` (same pair list / sampling as func_affine_scan): the
  question "f = p_i + p_j = g*h + r with g, h ANY affine functions of V_j (live wires + recent bits at j), r in V_j + V_end" is
  rewritten exactly as MinRank: on a basis v of V_j (control values put first), every degree<=2 representation of f is
  Q0 + span(K_1..K_k) (K = quadratic relations of the sampled reachable states, a superset of the true ones, so a rejection is
  sound), and g*h has an alternating quadratic part of rank <= 2. rank(B(l)) <= 2 <=> all 4x4 Pfaffians vanish (quadratic in l).
  k <= 18: all 2^k l enumerated; k <= 160: linearised (unknowns 1, l_i, l_i l_j), inconsistency = proof that no (g, h) exists;
  k > 160: only principal-submatrix necessary tests (too weak, see below). Sanity: on the original ops.json the merge2 pair
  21455/21459 is NOT rejected (consistent).
- Result on merge2 (n 3000, reps 2, maxgap 60), 71 pairs:
  - **25 pairs exactly rejected** (carry chains 21884..23478, k 73..157: the linearised Pfaffian system is inconsistent).
    This closes these pairs for ALL affine g, h of any weight; support_g_scan had only sampled the high-dim-G ones among them.
  - 2 dirty-CCCX pairs (25610, 28849): f is not even quadratic in V_j -> rejected (known artefacts).
  - 14 phase-tap pairs (early 15288..15417 k 631..711, fine 25746..25880 k 248..260): not decided by MinRank; already closed
    by the tap-wire argument (shared AND sits in another tap, needs an extra wire at width 62).
  - **30 pairs in 33038..34819 (lookup_c / late_curvature_norm chains, k 311..350): OPEN.** Linearisation would need ~60k unknowns;
    the principal-submatrix restrictions are always feasible because the relations (product wires) make almost every entry free.

## Exact block search closes the k~350 pairs (2026-11-08 23:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0823mm: PASS,
  score 100,568.57 = 20.650x** (`verify_p62_merge2_sv0823mm.json`, worst 0.99932 at x=161). Nothing was submitted to Kaggle.
- `minrank_sat.py` (MR_SAT=1 in minrank_core): CryptoMiniSat with native XOR clauses for `Q0 + sum l_i K_i = u^w`.
  Finds the merge2 witness instantly (21455/21459 on the original ops.json), but cannot prove UNSAT even for a k=154 pair that the
  linearisation rejects (600 s timeout). Kept only as a witness finder.
- Structure of the 30 open pairs (dumps via `MR_DUMP=prefix`): Q0 = c0^c1 + c2^c3 (weight 2), and only **36 of the 61 basis wires
  are touched by any relation** (the touched graph is ~K_36 minus 7 edges). So u^w (a complete 3-partite graph on the classes
  {u,w} = 10/01/11) must live inside that 36-wire block; any wire outside must be 00 (or u^w = 0, which means Q0 in span K: tested, false).
- `minrank_block.py dump.npz [--plant]` + `minrank_block.c`: eliminate l (equations c.(u^w) = c.Q0 for c in Ann(K), 280..284 of them),
  write each as u^T C w, and assign (u_a, w_a) vertex by vertex in reduced echelon form (GL2 symmetry removed). After m vertices,
  every equation whose entries all touch an assigned vertex is linear in the unassigned (u_R, w_R); the system is kept in echelon form
  incrementally (pivot = highest bit, interleaved bits, substitution clears the lowest bits) and any inconsistency prunes.
  Exhaustive => exact. Vertex order `ORDER=auto2` (Q0 wires first, then the reverse of the greedy order): the tree dies at depth 16.
  Self-test `--plant` (Q0 replaced by a random u^w + K l): the planted solution is found for 4/4 seeds (11k..189M nodes).
- **Result: all 30 pairs NONE(exact)** (25M..199M nodes, 42..235 s each; `minrank_block_results.txt`). Together with the 25 carry-chain
  pairs (linearisation), the 2 dirty pairs (not quadratic) and the 14 tap pairs (tap-wire argument), every same-target CCX pair of
  merge2 within maxgap 60 is now closed for arbitrary affine g, h (relative to the sampled relations, so rejections are sound).

## Chain 3->2 and non-adjacent pairs (2026-11-09 00:xx-01:xx UTC, supervisor)
- merge2 rebuilt (sha fc153f1f); **official verifier full 200,540,928 shots, salt sv0900mm: PASS, score 100,568.52 = 20.650x**
  (`verify_p62_merge2_sv0900mm.json`). Nothing was submitted to Kaggle.
- `chain_dump_scan.py` (MR_KMAX=0 MR_DUMP=prefix): MinRank systems for the chain sums F = p_i1 + ... + p_im of same-target CCX chains
  (carry L 3..6, k 73..157; lookup_c / late_curvature_norm L 3..7, k 311..350).
- `rank4_sat.py` (rank <= 2(L-1) witness search, CryptoMiniSat): planted rank-4 found at k=73 in 50 s, but NOT found in 100 s at k=154/349;
  real 21884 L=3 chain: TIMEOUT after 2400 s. Inconclusive tool for large k.
- `chain_rank_bound.py`: rank(Q0[:, untouched]) = 0 for all 39 chains -> no bound.
- Exact block search for rank 4 would need ~2^48 nodes (rank 2: 2^28). Chain 3->2 in general stays UNDECIDED.
- `nonadj_pair_scan.py`: decidable sub-case, non-adjacent pairs (ia, ic) of a chain (p_ib stays; same-target CCX commute).
  Lookup: **40 pairs, all NONE(exact)** via minrank_block (plant self-test on one dump: found, 284k nodes). Carry: **all lin-inconsistent**
  (exact reject). `nonadj_results.txt`.

## Star 3->2 / two-star 4->3 (2026-11-09 02:xx UTC, supervisor)
- merge2 rebuilt (sha fc153f1f); **official verifier full run, salt sv0902mm: PASS, score 100,568.59 = 20.650x**
  (`verify_p62_merge2_sv0902mm.json`). Nothing was submitted to Kaggle.
- New decidable sub-case of chain 3->2 (rank 4 is out of reach): one of the two new ANDs uses a basis wire v,
  F = v*w1 + u*w (w1, u, w arbitrary affine). Since v*w1 = sum_i w1_i (v^e_i), every entry (v, i) is free: drop the pairs that
  contain v and run the exact rank<=2 block search. `star_scan.py dump.npz out [v,...]` (dumps from `chain_dump_scan.py`,
  MR_KMAX=0 MR_DUMP=prefix, on merge2 with 3000 2 60). `STAR2=1`: two stars v1, v2 (F = v1 w1 + v2 w2 + u w, 4 -> 3; this also
  covers a 3->2 star on a mid-chain triple, since the left-over original AND is itself a star on its control).
- Self-test `star_plant.py` (plants v^w1 + u^w + K l): 3/3 HIT (296..665 nodes); two-star plant: HIT (653 nodes).
- **Carry L3 chains (7 chains, k 73..157, every touched vertex v): 196 / 196 NONE(exact)** (`star_carry_L3_results.txt`, < 1 s each).
- **Carry L4 chains, two stars (6 chains, all vertex pairs): 2526 / 2526 NONE(exact)** (`star2_carry_L4_results.txt`, ~10 min on 4 cores).
  So on the carry chains no 3->2 with a wire-star and no 4->3 with two wire-stars exists (relative to the sampled relations: sound rejections).

## Independent re-run (2026-11-09 01:05-03:00 UTC, overlapping supervisor run)
- merge2 rebuilt in a fresh container (sha fc153f1f); **official verifier full run, salt sv0901mm: PASS, score 100,568.50 = 20.650x**
  (`verify_p62_merge2_sv0901mm.json`). Nothing was submitted to Kaggle.
- Re-ran `nonadj_pair_scan.py` from scratch in a separate container: same result, 35 carry pairs lin-inconsistent, 40 lookup pairs
  NONE(exact) (`nonadj_results_rerun0901.txt`). `rank4_sat.py --T 2000` on the 21884 chain also as L=4 (R=3): TIMEOUT too.

## Star 3->2 (continued, 2026-11-09 02:xx UTC run)
- **Lookup L3 chain 33038-33122 (k 349), star on vertex v, ORDER=auto2: 9 of the 35 block vertices NONE(exact)**
  (v 0, 1, 2, 3, 18, 19, 20, 21, 22; ~2.4e8 nodes, ~5 min each; `star_lookup_33038_results.txt`). The greedy order (ORDER='') hits a
  4e8-node limit on v 0, so use auto2. Not done: the other 26 vertices of this chain and the other 8 lookup L3 chains
  (~35 x 5 min each, ~6.5 h on 4 cores in total), and two-star on the lookup L4 chains (C(35,2) per chain, not feasible this way).

## Star 3->2: lookup chain 33038 finished, general star centre on carry chains (2026-11-09 03:xx-04:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f); **official verifier full 200,540,928 shots, salt sv0904mm: PASS,
  score 100,568.53 = 20.650x** (`verify_p62_merge2_sv0904mm.json`). Nothing was submitted to Kaggle.
- Lookup L3 chain 33038-33122 (k 349): the remaining 27 vertices done (ORDER=auto2, ~2.4e8 nodes each) -> **all 36 touched
  vertices NONE(exact)** (`star_lookup_33038_results.txt`; the one LIMIT line is the old greedy-order attempt on v 0).
- `star_basis.py dump.npz out COMBOS`: star centre v = any XOR of basis wires (basis change x'_{c0} = v, A -> M^T A M, then the
  star_scan test). Plant self-test with v = 0+1, 2+5+9, 3+20: 3/3 HIT. Carry L3 chains (7), v in span of the 4 control values
  (11 non-basis combos each): **77 / 77 NONE(exact)** (`star_basis_carry_ctrl2_results.txt`). Weight-2 centres over the whole block
  (2961 combos): **2961 / 2961 NONE(exact)** (`star_basis_carry_pairs_results.txt`, ~1 s each).
- Lookup chain 33195 star (single basis centre) started: 8 / 36 vertices NONE(exact) so far (`star_lookup_33195_partial.txt`).

## Faster block solver; lookup star on 34604 (2026-11-09 04:06-05:05 UTC, overlapping supervisor run)
- merge2 rebuilt in another fresh container (sha fc153f1f); official verifier full run with the same salt sv0904mm:
  **PASS, score 100,568.5291 (identical to the other run's result, so the verifier is deterministic across containers)**
  (`verify_p62_merge2_sv0904mm_rerun.json`). Nothing was submitted to Kaggle.
- `minrank_block.c` sped up about 1.4x (45 s -> 32 s for 2e7 nodes): BMI2 `pdep` in spread(), the cleared basis rows are computed
  once per node and shared by the children, and the Su/Sw arrays are shared when the bit is 0 and updated only for equations
  that are not yet linear. The search order and pruning are unchanged: same stdout and node counts by depth at a 2e7 limit,
  the same full exact count on 34604 v0 (238,855,440 nodes), and the star_plant self-test on 34604 is 2/2 HIT (seeds 5, 11). Needs x86 BMI2.
  Profile note: the Su/Sw update loop is NOT the bottleneck (restricting it gave ~5%); the remaining cost is in insert() and the order.
- Lookup L3 chain 34604-34699 (k 346), single-wire star, ORDER=auto2: partial results in `star_lookup_rev_partial.txt`
  (all NONE(exact) so far; job list runs 34604 -> 34192 -> 33888, so it does not overlap the other run's 33195).

## Lookup star on 34604 finished; 34192 started (2026-11-09 05:06-06:xx UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f, identical); **official verifier full 200,540,928 shots, salt sv0905mm: PASS,
  score 100,568.544 = 20.650x** (`verify_p62_merge2_sv0905mm.json`). Nothing was submitted to Kaggle.
- Chain dumps regenerated from scratch (`chain_dump_scan.py p62mm.json 3000 2 60`, python3.13; same k per chain as before).
- Plant self-test on the new chain 34192 (`star_plant.py ... 7`, v 58): **HIT** (4.8e7 nodes).
- **Lookup L3 chain 34604-34699 (k 346): remaining 20 vertices done -> all 36 touched vertices NONE(exact)**
  (`star_lookup_34604_results.txt`, ~5 min each at 4 parallel jobs; the 5 vertices the overlapping 04:06 run also finished (31-34, 44) have identical node counts).
- **Lookup L3 chain 34192-34286 (k 311): all 35 touched vertices NONE(exact)** (`star_lookup_34192_results.txt`, ~3 min each).
- **Lookup L3 chain 33888-33963 (k 347): all 36 touched vertices NONE(exact)** (`star_lookup_33888_results.txt`).
- Lookup L3 single-wire star status: 33038, 34604, 34192, 33888 closed; 33195 8/36; 33329, 33481, 33623, 33763 not started.

## Lookup chain 33195 finished (2026-11-09 06:10-07:00 UTC, supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f); **official verifier full 200,540,928 shots, salt sv0906mm: PASS,
  score 100,568.526 = 20.650x** (`verify_p62_merge2_sv0906mm.json`, worst 0.99932 at x=161). Nothing was submitted to Kaggle.
- **Lookup L3 chain 33195-33267 (k 349): remaining 28 vertices done -> all 36 touched vertices NONE(exact)**
  (`star_lookup_33195_results.txt`, ~6.5 min each at 4 parallel jobs while the verifier ran, 2.39e8..2.41e8 nodes each).
- Lookup L3 single-wire star status: 33038, 34604, 34192, 33888, 33195 closed; 33329 4/36 (v 0-3 NONE(exact),
  `star_lookup_33329_partial.txt`); 33481, 33623, 33763 not started.

## 2026-11-09 07:10 UTC run (supervisor)
- merge2 rebuilt in a fresh container (sha fc153f1f); **official verifier full 200,540,928 shots, salt sv0907mm: PASS,
  score 100,568.527 = 20.650x** (`verify_p62_merge2_sv0907mm.json`, worst 0.99932 at x=161). Nothing was submitted to Kaggle.
- **Lookup L3 chain 33329-33403 (k 349): remaining 32 vertices done -> all 36 touched vertices NONE(exact)**
  (`star_lookup_33329_results.txt`, 2.39e8..2.42e8 nodes each, ~5 min each at 4 parallel jobs).
- Lookup L3 single-centre star status: 33038, 34604, 34192, 33888, 33195, 33329 closed; 33481, 33623, 33763 not started.
