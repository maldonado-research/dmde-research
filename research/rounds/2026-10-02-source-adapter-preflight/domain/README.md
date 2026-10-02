# Public frozen-source/grid diagnostic

The exact-muon-mass source callback and canonical coordinate/state mapping agree with the frozen source on identical nodes. A fixed full reference-domain native grid fails early source moments at all tested resolutions. A 1,001-coordinate short-window phase scan passes at N4001/8001, while N3001 fails. These are source-only diagnostics, not transported histories or production-consumption evidence.

Read [ADAPTER_DOMAIN_DESIGN.md](ADAPTER_DOMAIN_DESIGN.md) for the explicit mass roles, all-consumer map, observation callback, fixed-grid/JIT assumptions, retained failures and budget estimates.

- `source_grid_diagnostic.py` and `predeclaration.json`: native grid, exact-source callback, synthetic six-species arrays, nodal identity, moments and negative controls.
- `source_grid_refinement.py` and `refinement_predeclaration.json`: moving-endpoint phase sweep on fixed native grids.
- `results-first-declared/`: full-cap and isolated short-window source results, canonical snapshot arrays, source inventories and executed-code snapshots.
- `results-phase-refinement/`: retained failed JSON serialization attempt.
- `results-phase-refinement-corrected/`: first successful phase scan.
- `results-phase-pinned-replay/`: exact numerical replay after adding a clean pinned-source guard.
- `results-hardened-declared-replay/` and `results-hardened-phase-replay/`: final wrappers with explicit optimization refusal and full untracked-file source status; raw numerical arrays exactly match prior successful runs.
- `SCOPE_ADDENDUM.json`, `PINNED_REPLAY_RECEIPT.json`, `runtime.json`: provenance clarifications and runtime.
- `HARDENING_REPLAY_RECEIPT.json`: new wrapper hashes and replay/refusal evidence; original executed-wrapper snapshots remain unchanged.

No private input was used and no upstream file changed. The authored diagnostic is GPL-3.0-only; [LICENSE.txt](LICENSE.txt) retains the dependency's GPLv3 text. Output paths in reproduction commands must be fresh. Wrappers refuse `-O`, `-OO` and assertion-disabling `PYTHONOPTIMIZE`; use normal Python execution. This package does not run collision JIT, a production RHS/stepper, transport, weak rates, BBN or cosmological observables.
