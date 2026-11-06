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
