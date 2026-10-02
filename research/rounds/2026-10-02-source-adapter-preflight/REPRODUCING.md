# Reproduce the source-adapter preflight

These commands replay diagnostics, not physical trajectories. Use normal
Python, unset assertion-disabling optimization, and choose a fresh output
directory. Existing evidence must never be overwritten.

The separately installed official dependency is
`/workspace/shared/dmde-upstream/nudec`, pinned at
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` with all 21 tracked files clean.
Its GPL license is retained in the component bundles. The executed environment
is Python 3.12.14, NumPy 2.3.5, SciPy 1.16.3, Numba 0.63.1 and llvmlite 0.46.0.
No new root dependency declaration is required. The saved cloud install script
prepares this separate dependency environment.

Run from the public repository root:

```bash
python3 -B research/rounds/2026-10-02-source-adapter-preflight/verify_dossier.py
dmde_preflight_replay=$(mktemp -d /workspace/dmde-research/generated/preflight.XXXXXX)
export PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B research/rounds/2026-10-02-source-adapter-preflight/runtime/source_adapter_diagnostic.py run --source /workspace/shared/dmde-upstream/nudec --out "$dmde_preflight_replay/runtime"
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B research/rounds/2026-10-02-source-adapter-preflight/conservation/qed_component_reference.py --source /workspace/shared/dmde-upstream/nudec --output "$dmde_preflight_replay/qed-components.json"
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B research/rounds/2026-10-02-source-adapter-preflight/review/review_domain_artifacts.py --upstream /workspace/shared/dmde-upstream/nudec --domain research/rounds/2026-10-02-source-adapter-preflight/domain --output "$dmde_preflight_replay/domain-review"
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B research/rounds/2026-10-02-source-adapter-preflight/review/review_runtime_artifacts.py --runtime-results research/rounds/2026-10-02-source-adapter-preflight/runtime/results-serialization-fix --output "$dmde_preflight_replay/runtime-review"
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B research/rounds/2026-10-02-source-adapter-preflight/peer/review_runtime_receipts.py --bundle research/rounds/2026-10-02-source-adapter-preflight/runtime --source /workspace/shared/dmde-upstream/nudec --output "$dmde_preflight_replay/runtime-peer-review.json"
```

The root replay separately compares raw CSV bytes from the copied runtime
wrapper and QED observation values from the copied helper against their saved
receipts. Timing, absolute paths and new UTC timestamps are execution metadata;
their JSON bytes are expected to differ. Independent domain review uses
beta/incomplete-beta integrals rather than the producer's polynomial moment
expression. The domain folder preserves the full source-generation/refinement
wrappers and executed-code snapshots for deeper replay.

Each actual collision/grid configuration must launch in a fresh process:
Numba captures grid globals when compiling. Never change the momentum grid
inside a previously compiled collision trajectory and assume its kernels were
rebuilt. A larger fixed domain can undermine source and thermal resolution;
the full-domain failures are retained even though some short-window sampled
source-only configurations pass.

`verify_dossier.py` uses only the Python standard library. It verifies the exact
selected file inventory, canonical component manifests, successful saved local
adapter checks, known physics negatives, pressure-identity receipt precision,
and public-copy replay. It does not recompute native collisions, prove a
continuous error bound, validate a full EOS or run a BBN solver. Hosted CI runs
this identity/receipt check alongside the existing public numerical controls.
