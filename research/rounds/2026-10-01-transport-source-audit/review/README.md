# Separate skeptical review — 1 October 2026

[REVIEW.md](REVIEW.md) records the findings and limits. This is an internal, AI-assisted review of public diagnostics, not external peer review or a production-physics result.

The native coordinate, primary-muon multiplicity, neutrino/antineutrino factor, stopped-muon moments, source-constant mismatch and PRIMAT signed-energy map were independently checked. A fresh corrected native fixed-state fixture matches independently reconstructed source and averaged mixing to `3.04e-16` peak-scaled error. The continuum diagnostic reproduces across SciPy 1.16.3 and 1.17.0. All conclusions remain local or mathematical: no transport trajectory, weak-rate history or abundance is derived here.

The reference-table upper-clipping proxy is separate context. Its all-species injected source-energy loss is about `0.13035%`, compared with large local limiting losses. It uses the shipped reference table, excludes the lower grid cutoff and later redshifting, and is not the loss of a self-consistent production history. Table-panel quadrature and interpolation sensitivity are recorded explicitly.

Files:

* `independent_domain_review.py/json`: standard-library continuum, mass-shape and reference-table calculation; no provider/upstream imports.
* `table_proxy_sensitivity.py/json`: separate panel quadrature, time resolution and interpolation checks; no provider/upstream imports.
* `verify_review.py`: replays the two reviewer scripts and the authored continuum diagnostic, independently checks the final native raw fixture, and hashes the reviewed peer dossiers. It does not execute a native solver.
* `REVIEW_RECEIPT.json`: numerical checks, output-preservation controls, selected native fixture and reviewed peer hashes.
* `ARTIFACT_SHA256.json`: finalized reviewer files, excluding the manifest itself.

Reproduction requires Python 3.12, NumPy and SciPy for the sensitivity and verification scripts. Recorded verification uses Python 3.12.14, NumPy 2.3.5 and SciPy 1.16.3. Use the pinned public Nudec checkout at `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`, public PRIMAT checkout at `4bf97d5082eee54b9df50d88f43182bb651fea80`, and the unchanged public frozen source-card JSON. The receipt records input hashes.

Each script prints JSON by default and leaves the dossier unchanged. Optional `--output` creates a fresh receipt and refuses existing paths. Example commands, with paths adjusted to the local checkouts and dossier:

```bash
python independent_domain_review.py \
  --nudec-dir /path/to/nudec \
  --cards-file /path/to/dmde-research/provider/tables/DMDE_v099_blind_spectral_source_cards.json

python table_proxy_sensitivity.py \
  --nudec-dir /path/to/nudec \
  --cards-file /path/to/dmde-research/provider/tables/DMDE_v099_blind_spectral_source_cards.json

python verify_review.py \
  --nudec-dir /path/to/nudec \
  --primat-dir /path/to/primat \
  --cards-file /path/to/dmde-research/provider/tables/DMDE_v099_blind_spectral_source_cards.json \
  --source-audit-dir ../source-audit \
  --coverage-dir ../coverage \
  --native-probe-dir ../native-probe \
  --native-rhs-dir ../native-probe/results-2026-10-01-final-rhs/rhs_n21 \
  --output /tmp/dmde-review-fresh-replay.json
```

Select an unused output path for every saved replay. The saved first native normalization-label error, missing first-wrapper snapshot and earlier CLI-test packaging issues remain explicit in the native dossier. Corrected execution does not remove those historical limitations.
