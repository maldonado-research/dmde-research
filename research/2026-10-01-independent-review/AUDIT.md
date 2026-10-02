# Independent computational audit — DMDE continuation, 1 October 2026

**Disposition:** The six-process Born reference is mathematically and numerically consistent within its stated assumptions. The Standard Model control artifacts support successful upstream software executions with basic consistency checks. Neither result validates a DMDE mechanism or supplies a new observational prediction. This is an independent computational check by a separate agent, not external peer review.

Reviewed locations:

- `research/2026-10-01-equilibrium-audit/`
- Frozen `provider/code/dmde_v0920_validate_weak_rate_closure.py` and its public scope/causal-closure documentation.
- `research/2026-10-01-sm-control/runs/` (three successful control dossiers), wrapper and upstream output semantics.

## 1. Six-process equations: verified

Use massless neutrino energy p, electron energy E, Δ = 1.29333236 MeV and m_e = 0.51099895 MeV. In the infinitely heavy, unpolarized, nondegenerate-nucleon limit, the inverse of blocked neutron decay has the same phase space and normalization as neutron decay:

`λ_inverse = A ∫[0,Δ−m_e] dp p² (Δ−p) sqrt[(Δ−p)²−m_e²] f_e(Δ−p) f_antinu(p)`.

The outgoing nucleon is treated as unblocked. No extra occupation, spin or symmetry factor is needed relative to this paired Born decay coefficient. Energy support ends at Δ−m_e = 0.78233341 MeV. The antineutrino-capture channel has separate support p ≥ Δ+m_e = 1.80433131 MeV; these supports must not be confused.

The common normalization `A = (τ_n I0)^−1`, with

`I0 = ∫[m_e,Δ] dE E sqrt(E²−m_e²) (Δ−E)²`,

correctly recovers the vacuum neutron lifetime. For τ_n = 879.4 s, independent adaptive quadrature gives `I0 = 0.05700452626306701 MeV^5`, `A = 0.01994822223647636 s^−1 MeV^−5`. The producer's closed form agrees to 4.44e−16 relative difference. Normalizing to the measured lifetime does not restore absent energy-dependent radiative or other corrections.

For a common-temperature, zero-chemical-potential FD state, `f/(1−f)=exp(−E/T)`. The ratio of the reverse to forward **integrands** is `r=exp(−Δ/T)` for each of the following three pairs, and therefore also for each integrated pair:

1. electron capture / neutrino capture;
2. antineutrino capture / positron capture;
3. inverse beta decay / blocked beta decay.

If `N` is the sum of all three neutron-to-proton rates, the complete reverse rate is `rN`. The five-process reverse rate is `r(N−λ_beta)`. Thus the fractional deficit relative to the complete reverse rate equals `λ_beta/N`. The producer's formulas implement these statements correctly.

For arbitrary bounded antineutrino occupations, the coefficient identity `λ_beta−λ_inverse = A∫K_beta(1−f_e−f_antinu)dp` and bound `0≤λ_inverse≤A∫K_beta f_e dp` remain correct. The coefficient difference alone is **not** a physical net neutron-production rate. A collision term requires the separate neutron and proton populations, for example `n_p λ_inverse−n_n λ_beta` for that reaction pair.

## 2. Independent numerical verification

The independent script `independent_rates.py` in this audit directory integrates in **electron energy** with SciPy adaptive quadrature, including capture integrals to infinity. It does not import the producer or frozen validator. Its results are in `independent_rates.json`.

I then compared all six resulting coefficients against the producer's Gauss–Legendre implementation, which uses different variables/endpoint substitutions and finite thermal tails. Maximum absolute relative difference over the original producer table (0.02–10 MeV) was **5.11e−15**. `producer_comparison.json` records the pointwise comparison. The added 0.25 MeV reference values also match:

| Common T (MeV) | Inverse rate (s^−1) | Five-process p→n rate (s^−1) | Inverse/five-process rate |
|---:|---:|---:|---:|
| 0.30 | 1.15822140303346e−5 | 1.19119167989708e−4 | 0.0972321602459 |
| 0.25 | 5.25030696535185e−6 | 2.34812031494601e−5 | 0.223596164640 |
| 0.20 | 1.54448114547887e−6 | 2.53871841341660e−6 | 0.608370403475 |
| 0.10 | 2.67194783913872e−9 | 2.39046724845279e−10 | 11.1775128518 |

Independent root finding places inverse/five-process = 0.10 at **0.298175736398997 MeV**, agreeing with the producer. At 0.20 MeV, the omitted fraction relative to the *complete* reverse rate is instead **0.378252672494**, not 0.60837. These denominators must stay explicit.

All 13 producer unit tests passed on independent execution. The report's 96→192 quadrature refinement and 60T→80T tail refinement changed rates by at most about 1.60e−14 on the checked table. The frozen five integrands agree after matching normalization to about 1.20e−14. Their small raw ~2.34e−8 normalization difference is consistent with the frozen unsmoothed 256-node vacuum quadrature; it is not a material physics discrepancy.

The deliberately clipped 10T-tail negative control is scientifically useful: common truncation preserves reciprocity while biasing absolute capture rates. Exact detailed balance is necessary in this restricted reference state but insufficient as an accuracy/domain-completeness test.

## 3. Frozen v0.9.20 contract: scope of the finding

The omission is **already explicitly documented** in the public v0.9.20 scope notes. This work quantifies that known scope limit and supplies a reproducible reference; it does not discover new weak physics or demonstrate a new hidden backend error.

The frozen validator requires three neutron-to-proton columns, two proton-to-neutron columns, and exact column sums. A physically complete reverse total containing inverse beta cannot equal the sum of only the two genuine reverse-capture columns. Simply adding the missing inverse rate to the total fails this sum check *before* the Born direction-total gate. Relabeling the inverse contribution as a different physical process would change the ontology.

The 10% comparison uses the five-process reference as denominator. Its history-dependent mask is `reference >= max(1e−18, 1e−10 * peak(reference))`. At the table's 10 MeV peak (~84934.17 s^−1), this is ~8.4934e−6 s^−1: the 0.20 MeV five-process coefficient is masked, whereas the 0.25 MeV coefficient is above the mask and its reference discrepancy exceeds 10%. Producer documentation was revised to preserve this distinction.

This audit does **not** submit a complete synthetic provider-return bundle or assert a specific full-validator outcome for a production history. A future six-process production contract must deliberately revise column ontology, shapes, metadata, sums, bridge checks and adapters together; changing the published frozen reference silently would compromise provenance.

## 4. Physics and inference limits

- Equal bath temperatures and zero chemical potentials are essential to the simple `exp(−Δ/T)` ratio. Decoupled neutrinos, nonthermal injection and nonzero chemical potentials generally require direct occupation-dependent integration. The actual standard cosmology below neutrino decoupling does not satisfy the equal-temperature fixture.
- Independent negative example: at `T_gamma=0.1 MeV`, `T_nu=(4/11)^(1/3)T_gamma`, the complete reverse/forward rate divided by `exp(−Δ/T_gamma)` is about **0.252696**, not one. This is expected nonequilibrium behavior, not a detailed-balance implementation error.
- The beta/inverse support is low neutrino energy. A 52.83 MeV injected endpoint does not directly enter this inverse-beta integral; any low-energy occupation effect requires a demonstrated transport history.
- Recoil, weak magnetism, finite nucleon mass, Coulomb/radiative corrections, thermal plasma corrections and nuclear reaction-network evolution are absent from the standalone Born reference. The code's excellent quadrature agreement does not set the physical accuracy of the approximation.
- The beta-minus-inverse identity is a difference of coefficients, not a conserved energy diagnostic or an abundance solution. No background expansion, neutrino transport, nucleosynthesis response, perturbation growth or gravitational lensing is calculated by this audit.
- Large late relative reverse-rate differences can involve minuscule absolute rates. They do not imply appreciable helium/deuterium changes. The reference provides no bound on a DMDE source's abundance response or observational viability.
- No new mathematics, particle mechanism, fitted cosmological parameters, dark matter/dark energy explanation or discovery follows from these results.

## 5. Standard Model control artifacts: limited verification

I independently read the three result/configuration/provenance sets and recomputed SHA-256 for every file then listed in their output manifests; all matched. The wrapper records actual Git commits, tracked-file hashes, Python/package versions, effective settings and a runner snapshot, and refuses a dirty source checkout. This is adequate provenance for the stated source/cache-backed control exercise, subject to preserving logs and manifests in their final form.

The selected settings include `Omegabh2=0.02242`, Python backend, radiative/finite-mass/thermal corrections enabled, and shipped weak-rate caches allowed. The actual upstream default neutron lifetime is **878.4 s**; the separate Born diagnostic uses **879.4 s**. These are distinct controls, not a shared calibration or direct precision cross-comparison.

| Upstream commit / network | Y_p | D/H | N_eff |
|---|---:|---:|---:|
| 4bf97d5082eee54b9df50d88f43182bb651fea80 / small | 0.24699894798444227 | 2.435860013230952e−5 | 3.0439772985579183 |
| 908028da9426370f2f41ca996503650eef34795a / small | 0.24699894798444227 | 2.435860013230952e−5 | 3.0439772985579183 |
| 4bf97d5082eee54b9df50d88f43182bb651fea80 / large, amax=8 | 0.24700235492652864 | 2.4365286436668656e−5 | 3.0439772985579183 |

The equality of two small-network runs demonstrates agreement under these software/settings/cache conditions. It is not an independent weak-rate derivation, a cache-free rebuild, a full backend cross-validation, or a physical uncertainty estimate. Small-versus-large network changes likewise are not an error bar.

All three abundance tables have 500 rows, of which the first **64** have all abundances zero. I confirmed the upstream implementation explicitly fills rows before nuclear-network initialization with zeros. The first active row is index 64 at `T_gamma≈9.90256 MeV`. These padding rows are not physical baryon evolution and must be excluded rather than interpreted as a conservation violation or silently treated as real abundances. The maximal `|Σ A_i Y_i−1|` on active rows is ~1.65135e−12 for each small run and ~1.65379e−12 for the large run. Final abundances agree with this sanity check. These checks do not establish energy conservation or a cosmological likelihood.

The originally captured large-run `checks.json` has null baryon-check fields because its original wrapper lacked the complete mass-number map. I independently recomputed the large-network sum using all 12 species, obtaining final absolute error 1.64890e−12. Preserve the original receipt and make any corrected interpretation explicit; do not rewrite it as if the first check had executed.

A previously published bare control summary has different numbers, but its full configuration/output provenance is unavailable in that summary. Preserve this discrepancy. The present pinned-commit rerun does not reproduce that historical numerical claim; it is not justified to attribute the discrepancy to an identified cause or overwrite it silently.

## 6. Assessment and next required evidence

No blocking formula or numerical errors were found in the reviewed six-process reference. The contract-denominator/masking, coefficient-versus-population and control-lifetime distinctions above are material interpretation constraints. The reviewed control receipts establish a useful reproducible baseline but no DMDE result.

The next decisive development is explicit six-process integration using the transported occupations, with preserved source identity, correct momentum support, endpoint/refinement evidence, corrected production rates and a documented handoff to the nuclear network. A paired baseline/source calculation and appropriate convergence controls are required before claiming any abundance response. Broader conservation, expansion, growth, lensing and observational tests remain separate evidence requirements.

Artifacts in this audit directory (`independent_rates.py`, `independent_rates.json`, `producer_comparison.json`, `control_artifact_checks.json`) support the independent checks. No private archive inputs or personal documents were used in these calculations or this report.

## Final documentation/receipt review

The completed SM README and `verify_controls.py` were inspected; the verifier passed on all three saved dossiers. Its background check establishes equality of the exported density-component sum to the exported total, not an independently solved conservation equation. The README uses the appropriately narrow description. Its explicit cache reuse, wrapper-recording failures, different lifetime, original null check and unresolved historical-scalar mismatch preserve relevant negative evidence.

`research/README.md`, `CLAIM_LEDGER.md` and `NEXT_TESTS.md` were also reviewed. Their conservation/acceleration argument is conditional on ordinary GR, a pressureless decaying parent, relativistic daughters, nonnegative densities and no additional sector. Under those assumptions the summed homogeneous continuity equation and `a_ddot/a = −(4πG/3)(rho_parent+2 rho_daughters)` are correct. This conditional result does not constrain unspecified vacuum or modified-gravity additions. The documents make this limitation explicit and distinguish prospective tests from completed work. No material scientific overclaim was found.

After the 0.25 MeV row was added, the numerical comparison was regenerated for all 13 table temperatures; the maximum relative disagreement remained **5.11e−15**. Independent audit runtime: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0. This differs from the control-run runtime recorded above and in its provenance. Final reviewed-file hashes are recorded in `reviewed_sources_sha256.json`.

### Reproduction interface follow-up

The control verifier now defaults to stdout only and permits an explicit new
`--output` path. Independent rechecking confirmed that default execution leaves
the full control dossier byte-identical, optional output creates a fresh receipt,
and an existing destination is rejected without modification. All 42 files in
the final SM artifact manifest verified successfully.

The independent integrator was likewise changed to stdout-only default with an
optional new output path. Its original `independent_rates.json` is preserved;
fresh numerical output matches the original. The new
`compare_with_producer.py` performs the full 13-temperature comparison and records
executed code hashes without altering either dossier. Both commands' explicit
output modes and overwrite refusals were checked. The README provides commands
with outputs outside the published directory. These are recording-interface
changes; physical formulas, original results and original receipts are unchanged.
