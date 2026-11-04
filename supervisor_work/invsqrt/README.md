# invsqrt — supervisor work branch

Independent improvement of the **official reference** Newton–Raphson circuit
(`data/verifiers/invsqrt/nr_reference_circuit.py`), with my own code only (no third-party notebook code).

## Changes vs reference
1. **Precision search** (`prec_search.py`): coordinate descent over `Precision` widths, scored with an
   exact replica of the verifier cost formula (matches the official reference cost to 1e-6).
   Best: `delta=13, coef=17, square=27, product=28, result=28` (worst err/tol 0.789).
2. **Lazy allocation** (`variant.py`): registers allocated just before use and freed right after;
   `c3` is Clifford-loaded only for Horner step 1 and unloaded immediately.
3. **drop_square**: `y0^2` is uncomputed right after `z = M*y0^2` and recomputed before uncomputing `z`
   (−28 qubits at the peak, +2 squaring passes).
4. **drop_horner**: Horner intermediates `r2`, `r1` are uncomputed once `y0` is known (−34 qubits,
   +4 Horner steps).

## Results (official verifier, 200,540,928 shots, default salt, run on 4-core Linux)
| file | Q | Toffoli | C | cost | × ref | verifier |
|---|---|---|---|---|---|---|
| reference | 260 | 7735 | 7987.59 | 2,076,774.23 | 1.000 | PASS |
| invsqrt_sv_A.kmb (`13,17,27,28,28 1`) | 212 | 8281 | 8530.53 | 1,808,472.20 | 1.148 | PASS |
| invsqrt_sv_B.kmb (`13,17,27,28,28 1 1`) | 178 | 9633 | 9882.53 | 1,759,090.20 | 1.181 | PASS |

## Reproduce
```
python3.13 supervisor_work/invsqrt/make_cand.py OUT.kmb 13,17,27,28,28 1 1   # B; drop last arg for A
PYTHONPATH=data/kickmix python3.13 data/verifiers/invsqrt/verify_submission_invsqrt.py OUT.kmb
```
`data/kickmix/kickmix.so` is a CPython 3.13 Linux x86 build (fails to import on 3.11/3.12). Needs numpy+scipy.
Builds are byte-for-byte deterministic (A sha256 8a1faebe…9be4b).

This is far from the public best (≈20×, 63 qubits; QROM 256-segment + addition/lookup design). See SUPERVISOR.md
on branch `claude/supervisor` for next directions. Nothing here was submitted to Kaggle.
