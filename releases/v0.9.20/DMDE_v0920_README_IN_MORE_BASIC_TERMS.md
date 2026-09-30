# DMDE v0.9.20: Five-Channel Weak-Rate Closure and Frozen-Pair Differential-Response Design

Source release: 17 August 2026. Public note prepared: 5 September 2026.

## In More Basic Terms

This release improves the checks used to test a dark-matter and dark-energy hypothesis. It keeps two proposed particle-injection scenarios fixed and makes it harder for a computer calculation to pass while leaving out important reactions or failing to carry the injected particles through the calculation correctly. It also shows how closely the two scenarios are matched and estimates the numerical precision needed to compare their effects. These are improvements to the test and its reliability. They do not yet show that the hypothesis explains dark matter, dark energy, or a unified theory of everything. The next step is to run the complete particle-transport and early-universe element-formation calculations, validate the returned evidence, and compare independent implementations.

## Release description

DMDE v0.9.20 is a source-frozen validation and numerical-design release for a blinded two-card neutrino-spectrum to Big Bang nucleosynthesis (BBN) test. It repairs a reproduced synthetic v0.9.19 false pass in which both charged-lepton capture channels were omitted and unblocked vacuum beta decay was returned at all temperatures. The new contract independently recomputes audit-only, neutron-lifetime-normalized Born histories for all five exported weak processes, applies per-process and direction-total envelopes, and checks the relevant threshold and endpoint refinement. It retains source-shape and time-integral closure, source-on/off production-stepper witnesses, and BBN input-consumption canaries. A companion source-only result derives the frozen pair's exact differential-response geometry and conditional numerical-precision requirements. The physical source payloads and model parameters remain unchanged. The public packet contains the blinded provider files, validators, schemas, templates, documentation, and receipts. It contains no production helium, deuterium, or effective-neutrino-number result.

## What changed

- All five exported weak-process histories receive independent Born-envelope checks: neutrino capture, antineutrino capture, positron capture, electron capture, and neutron beta decay.
- Each non-negligible process has a 25% audit envelope; each neutron-to-proton or proton-to-neutron direction total has a tighter 10% envelope. Finite-temperature beta blocking and the late neutron-lifetime gate remain explicit.
- The momentum grid must meaningfully refine the antineutrino-capture threshold at 1.80433131 MeV and the beta-decay endpoint at 0.78233341 MeV.
- Earlier source-shape, source-time, transport-stepper, meaningful-refinement, and BBN-consumption evidence requirements remain in force.
- The source-only frozen-pair calculation gives an exact response identity and makes the numerical precision needed for future endpoint comparisons explicit.

## Scope and limits

- No production Y_p, D/H, or N_eff prediction is bundled or implied. No confirmation of DMDE or a unified theory follows from these checks.
- The Born envelopes are execution checks, not a complete corrected weak-rate calculation. The frozen five-column export does not separately represent the inverse three-body process p + e- + antineutrino -> n.
- Passing cannot prove that evidence was not fabricated or that transport, radiative, recoil, plasma, or nuclear-network physics is complete. Independent replay, physical review, and backend replication remain necessary.
- The pair calculation determines a direction in source-amplitude space. It does not determine the sign or magnitude of any abundance response. Its neutrino coordinate includes linked source-energy and parent-density effects.

## Files and verification

The provider ZIP is the exact original v0.9.20 artifact, with no payload, parameter, code, or scoring changes. The public verification JSON records fresh local checks and their limits. The SHA-256 CSV covers every other file in this public release set and excludes itself. The analyst archive, complete upgrade archive, outer archive, and private scoring/unblinding material are not part of this public set.

## Next scientific evidence

Execute both blinded scenarios with momentum-resolved transport and an instrumented BBN network. Return complete source, operator, spectra, rate, network-consumption, and refinement evidence. Validate the returned artifacts before interpreting endpoint differences; obtain independent replay and replication. The package does not include or simulate these missing production results.

## Source documents

Within the provider ZIP: README_PROVIDER_DISPATCH.md; docs/DMDE_v0920_WEAK5_CLOSURE_AND_FALSE_PASS.md; docs/DMDE_v0920_FROZEN_PAIR_DIFFERENTIAL_RESPONSE_RESULT.md; docs/DMDE_v0920_VALIDATION_SCOPE_AND_LIMITS.md.

Earlier record identified by the author: https://zenodo.org/records/20187862. Publication of a successor must be verified separately; this note alone is not a publication receipt.
