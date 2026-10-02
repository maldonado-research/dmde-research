# Native Nudec diagnostic receipt — 1 October 2026 (America/Los_Angeles)

Actual unmodified native emission and coupled RHS calls completed. These are bounded diagnostics, not time-integrated transport, a BBN calculation, or a production witness.

The primary RHS receipt is **`results-2026-10-01-final-rhs/`**. The emission receipt is **`results-2026-10-01/`**. The first RHS in that emission directory had a normalization-label error; its raw arrays and metadata are preserved, and its interpretation is corrected below. The intermediate corrected RHS in `results-2026-10-01-corrected-rhs/` is retained as well.

## Source and execution

The separately installed source cache is `/workspace/shared/dmde-upstream/nudec`, with HEAD `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` and tree `fa965d26fb6cc71142b1d4108e442c99cb88cb1c`. Before/after receipts contain SHA-256 hashes for every tracked source file, and identical empty tracked/untracked Git status. No upstream or research repository files were edited. No external source is bundled here.

Runtime: Python 3.12.14, NumPy 2.3.5, SciPy 1.16.3, Numba 0.63.1, llvmlite 0.46.0. Bytecode writing is disabled; BLAS, OpenMP, NumExpr and Numba thread limits are one. The run records imported native module paths and hashes, and actual Numba nopython collision signatures. Each grid configuration starts a fresh subprocess because Numba can capture grid globals. Each worker has a declared 180-second limit.

The final RHS executed `native_probe_final.py`, SHA-256 **`362708741fb0d04a658f0aec5886a07ba1e0d983b6e26e222f996bebf07f27d2`**. Its exact bytes are saved as `results-2026-10-01-final-rhs/executed_wrapper.py`, alongside the runtime hash and command. The first emission run did not save an executed wrapper hash or snapshot: its native source provenance and raw outputs are recorded, but the final wrapper must not be claimed to have produced that first receipt. The final wrapper differs in corrected branching labels and CLI evidence-preservation checks; emission formulas and declared grids were unchanged.

The wrappers use GPL-3.0-only SPDX headers. Native-source attribution, constants and licensing remain in the external checkout. The official source README credits Kensuke Akita, Gideon Baur and Maksym Ovchynnikov and requests citations to arXiv:2411.00892 and arXiv:2411.00931.

The canonical artifact identity receipt is **`artifact_sha256_complete.json`**. It hashes every artifact present before its creation and excludes itself. The older top-level `artifact_sha256.json` is retained as a known packaging error: it accidentally included an empty-file self-hash while being written, so it must never be treated as a passing complete identity check. Its self-entry fails verification. The per-run manifests exclude themselves correctly. The canonical receipt is refreshed after documentation changes without modifying raw numerical evidence.

## Emission measurement

Declared inputs are `x_stop=4`, `x=nextafter(4,0)`, `q_min=0.01`, unit muon decay probability, and `n=65,129,257,513,1025`. Actual `Momentum_Grid.setupGrid` and `Distributions.muonDistribution` produce the three-flavor arrays; the tau source is exactly zero before oscillations. Samples and native quadrature weights are retained in every `source_samples.csv`. Nothing is renormalized.

The native RHS converts its grid coordinate by `p=q*me/x`, using native `me=0.5109989 MeV` and `mmu=105.7 MeV`. Thus physical integration uses `dp=(me/x)dq`. The tested native endpoint is `q_max=x_stop*mmu/2`, while complete support requires `q_max=x_stop*mmu/(2*me)`. Their physical upper endpoints in the declared left limit are 27.006291865 MeV and 52.85000000000001 MeV. The physical muon endpoint is 52.85 MeV. The emission function itself does not apply the cutoff gate: this is the limit as x approaches the stop from below; `System_Nudec` has the strict gate `x<stopPoint`, so injection is off at exactly the stop.

Exact primitives for `u=2p/mmu` are `N_e=4u^3-3u^4`, `N_mu=2u^3-u^4`, `E_e=(3mmu/10)(5u^4-4u^5)`, and `E_mu=(mmu/20)(15u^4-8u^5)`. Bounds are intersected with physical support. The wrapper also records native and exact moments through p^5.

| Exact physical moment | Electron flavor | Muon flavor |
|---|---:|---:|
| Full number per muon | 1 | 1 |
| Full energy, MeV | 31.71 | 36.995 |
| Native-domain retained number | 0.329177108595 | 0.198680349067 |
| Native-domain retained energy, MeV | 6.39118191457 | 3.93214532508 |
| Native-domain energy fraction | 0.201550990683 | 0.106288561294 |

The upper-domain loss is about 67.08% and 80.13% of number, and 79.84% and 89.37% of energy, respectively. These are absolute analytic deficiencies in each unrenormalized spectrum; they do not depend on LLP abundance or branch normalization. The omitted lower interval starts at `p_min=0.00127749725 MeV` and loses approximately `5.6493e-14` electron-flavor number and `2.8247e-14` muon-flavor number. Low-momentum energy losses are also recorded explicitly.

| Complete-domain n | Native muon-flavor number | Native muon-flavor energy, MeV | Native muon-flavor p^5 / full p^5 |
|---:|---:|---:|---:|
| 65 | 0.989583585127 | 36.4444907941 | 0.965909824305 |
| 129 | 0.994791792565 | 36.7197461320 | 0.982954951793 |
| 257 | 0.997395896300 | 36.8573731131 | 0.991477478475 |
| 513 | 0.998697947773 | 36.9261865411 | 0.995738738592 |
| 1025 | 0.999348976120 | 36.9605933750 | 0.997869373895 |

The complete-domain final node is one representable step above physical support in this left-limit call. Native `searchsorted` therefore zeros that node. The electron spectrum tends to zero at the endpoint, while the muon spectrum has a nonzero left-limit `4/mmu`; losing its final weighted sample gives the observed approximately 1/n deficit. This behavior was preserved without moving x, altering the endpoint, substituting weights or rescaling samples. At n=1025 the complete-domain muon p^5 deficiency remains about 0.213%; the native clipped-domain p^5 fractions are only about 0.02283593817 and 0.00795571757. Native electron number/energy at n=1025 are 1.000000001002 and 31.71000004052 MeV; small excesses reflect floating-point native quadrature, not a normalization adjustment. `emission_moment_summary.csv` contains every refinement and moments p^0 through p^5. Successful execution is distinct from source completeness; the clipped case fails completeness decisively.

Threshold records use the same declared frozen static Born heavy-nucleon convention: `Delta=1.29333236 MeV`, reference electron mass `0.51099895 MeV`, antineutrino proton threshold `1.80433131 MeV`, and neutrino neutron threshold zero. This threshold reference electron mass differs slightly from the native coordinate mass; both are recorded. Exact full/retained above-threshold moments are saved. These are threshold moments, not weighted capture rates or finite-recoil cross sections. For electron flavor above the antineutrino threshold, full number/energy are 0.999844901101 and 31.70979048035 MeV; clipped retained values are 0.329022009696 and 6.39097239492 MeV.

## Corrected coupled RHS fixture

The final receipt calls actual `System_Nudec`, native thermodynamics and thermal QED functions, native oscillation mixing, and native Numba collisions at fixed `x=4`, `z=1.4`, `t=1 s`, and a tiny complete-domain linear n=21 grid. All flavors have `f(q)=1/(exp(q/z)+1)`. LLP controls use comoving count zero or `1e-5`, mass 300 MeV and lifetime 10 s. **The corrected native branch is 0.8**, equal to average primary muon multiplicity 0.8; all other branches are zero. An externally assumed equal-charge pair convention labels this B=0.4. Native `SingleShot` passes the multiplicity through directly, and the native RHS independently supplies the neutrino/antineutrino factor 1/2.

Native code copies each neutrino spectrum to its antineutrino spectrum; independent charge asymmetry is not evolved. No CP or charge-asymmetric injection is demonstrated.

| Native control | dz/dx | dt/dx, seconds | Full 65-component vector |
|---|---:|---:|---|
| Zero LLP, gate off | 0.0594125817366 | 26.5364245478 | Finite |
| Zero LLP, gate on | 0.0594125817366 | 26.5364245478 | Finite, bitwise equal to off |
| Positive LLP, gate off | 0.0594125817366 | 26.4273503306 | Finite |
| Positive LLP, gate on | 0.0623332476522 | 26.4273503306 | Finite |

At positive count, on-minus-off maximum neutrino derivative difference is `2.1248871136108562e-11`, photon derivative difference is `0.00292066591560948`, and time derivative difference is zero. Positive-count off minus zero-count off changes `dt/dx` by `-0.10907421719777943 s`, through native LLP energy density in the Hubble rate. Gate on is `stopPoint=nextafter(x,+inf)`; gate off is `stopPoint=0`. This native gate changes both neutrino source injection and the LLP energy-loss term in the photon equation. It is a diagnostic native gate control, **not a frozen-only source-toggle certification**.

Instrumentation wraps each actual `getDistribution` callable, records a copy of its returned preoscillation array, and returns the exact native object unchanged. RHS, collisions, mixing and thermodynamics are not replaced or mocked. All five native source callables execute even for zero branch coefficients. In particular, the zero-coefficient direct-tau callable can have a nonzero raw tau array; the actual branch-weighted combined source, recorded separately, has exactly zero tau before oscillations. Zero-count gate-on records nonzero source shapes but their common native LLP amplitude is zero.

The tiny grid severely under-resolves the FD bulk. Finite native execution and the matched controls do not establish thermal precision, grid-converged transport, conservation along a trajectory, kinetic evolution, capture feedback, Neff, elemental abundances, or any production run. No time integrator or full Standard Model solve was invoked.

## Preserved normalization error and CLI checks

The first RHS receipt supplied native branch **0.4**, so its actual primary muon multiplicity was **0.4**, and an equal-charge pair interpretation would be **B=0.2**. Its metadata incorrectly labeled primary multiplicity 0.8 and claimed that native code converted this to branch 0.4. `results-2026-10-01/metadata_erratum.json` records the mistake; raw results were not rewritten. Emission is unit-probability per-muon shape and is unaffected. The intermediate and final corrected receipts both supply branch 0.8, with identical numerical fixture outputs. Only the final receipt is the primary RHS evidence.

The final CLI refuses optimized Python, invalid grids, missing grid arguments and existing output paths; aggregate worker failures/timeouts propagate a nonzero process result. Six harness checks pass in `cli-checks-2026-10-01-r2/result.json`, including a controlled worker failure that calls no native physics. The first harness test failed because its test double inadvertently intercepted Git provenance reads; the diagnosis and original artifacts remain in `cli-checks-2026-10-01/`. This was a harness-test defect, not a native physics failure. No real native diagnostic worker failed or timed out.

For a repeat, use a fresh output path and the final frozen wrapper:

```bash
PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 /workspace/shared/dmde-upstream/nudec-venv/bin/python -B /workspace/shared/dmde-native-probe/native_probe_final.py run-rhs --source /workspace/shared/dmde-upstream/nudec --out /workspace/shared/dmde-native-probe/new-rhs-receipt
```

`run` additionally executes the unchanged declared emission refinements. `--source` permits another clean checkout of the declared commit. Results are local diagnostics, and saved configuration or publication readiness is not inferred from them.
