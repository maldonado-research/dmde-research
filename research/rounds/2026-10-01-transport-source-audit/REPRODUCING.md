# Reproduce the reviewed public round

Run from the DMDE repository root. Keep every historical receipt intact and
choose a new output path. The isolated dependency environment used in this
round is `/workspace/shared/dmde-upstream/nudec-venv`, with Python 3.12.14,
NumPy 2.3.5, SciPy 1.16.3, Numba 0.63.1 and llvmlite 0.46.0.

The clean public source checkouts are Nudec at
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` and PRIMAT at
`4bf97d5082eee54b9df50d88f43182bb651fea80`. The reusable cloud setup script
installs these caches separately from the three project checkouts. Do not
change the frozen provider or substitute a new upstream revision silently.

Verify recorded identities without importing a solver:

```bash
python3 research/rounds/2026-10-01-transport-source-audit/verify_dossier.py
```

The verifier checks the canonical manifests. The native dossier's original
top-level `artifact_sha256.json` has a documented bad self-hash; it is preserved
as negative packaging evidence. Its corrected canonical manifest is
`artifact_sha256_complete.json`. A generic recursive demand that every historic
manifest pass would misclassify this deliberately retained error.

Replay the continuum calculation and its command-interface controls:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  research/rounds/2026-10-01-transport-source-audit/coverage/verify_coverage.py \
  --output generated/my-new-coverage-verification.json
```

The verifier requires exact scientific/source fields and permits explicitly
recorded runtime-version differences. The saved scientific receipt used
SciPy 1.17.0; the prepared runtime uses 1.16.3. Both were executed successfully.
Optimized Python and overwriting receipts are refused.

Replay the native emitter refinements and the corrected local RHS:

```bash
PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 \
  /workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  research/rounds/2026-10-01-transport-source-audit/native-probe/native_probe_final.py \
  run --source /workspace/shared/dmde-upstream/nudec \
  --out generated/my-new-native-transport-diagnostic
```

`run-rhs` executes only the corrected local RHS. `run` makes 11 separate
worker calls: ten declared source-domain/refinement cases and one RHS fixture
containing four matched controls. It saves its executed wrapper bytes, source
hashes, runtime, commands, raw data and worker failures. `run` does not evolve a
trajectory. `public-copy-replay/` records the executed replay of this public
copy: all 11 jobs pass and 16 numerical sample/state/vector files exactly match
the named baseline records. The preceding copy/command setup error is retained
and is distinguished from native execution.

The original native CLI harness writes a dated directory beside its wrapper.
To repeat it, copy `check_cli.py` and `native_probe_final.py` into a new scratch
directory and run the copied `check_cli.py` there. Do not run it against the
archived dossier and expect to overwrite its existing harness evidence.

The separate reviewer can replay its independent source/domain/table arithmetic
and inspect the corrected raw RHS without importing the native solver:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  research/rounds/2026-10-01-transport-source-audit/review/verify_review.py \
  --nudec-dir /workspace/shared/dmde-upstream/nudec \
  --primat-dir /workspace/shared/dmde-upstream/primat \
  --cards-file provider/tables/DMDE_v099_blind_spectral_source_cards.json \
  --coverage-dir research/rounds/2026-10-01-transport-source-audit/coverage \
  --source-audit-dir research/rounds/2026-10-01-transport-source-audit/source-audit \
  --native-rhs-dir research/rounds/2026-10-01-transport-source-audit/native-probe/results-2026-10-01-final-rhs/rhs_n21 \
  --native-probe-dir research/rounds/2026-10-01-transport-source-audit/native-probe \
  --output generated/my-new-transport-review.json
```

The local source reconstruction conditions on the measured `dt/dx` and emitted
arrays; it does not separately certify the thermodynamic Hubble calculation.
Reference-table history weighting is a proxy, not a recomputed injected
background, an energy-conservation history or a BBN calculation.
