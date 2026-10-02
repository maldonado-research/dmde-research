# Independent adapter review — 2 October 2026

Ricardo Maldonado's research program. This is a separate internal review
prepared with AI assistance, not external peer review. It uses public source,
public specification documents and declared diagnostic inputs only. No blind
payload, private archive, weak history, nuclear network or abundance is used.

The source/reference-entropy adapter checks pass in their declared diagnostic
scope. A real native unsplit RHS mixes the source before returning it and
cannot directly satisfy the frozen per-species comparison to pre-mixing source.
The tested coarse real-RHS grid also fails the frozen source moment ceiling.
No finite-step h/h2 gate or cosmological trajectory was run.

The canonical final evidence is:

- `domain-guarded-final-review/domain_artifact_independent_review.json`:
  all 3,003 phase-scan rows independently recomputed with beta/incomplete-beta
  references; strict bindings to the producer's hardened final source bytes.
- `runtime-guarded-final-review/runtime_artifact_independent_review.json`:
  all 78 raw runtime manifest members verified, and source coefficient,
  actual-time gate, symmetry aliases and state conversion independently checked.
- `mixing-guarded-final-review/frozen_stepper_mixing_probe.json`:
  35 declared physical T/p points, actual native mixing, and an independent
  explicit PMNS construction, with the clean pinned upstream checked.
- `FROZEN_STEPPER_REVIEW.md`: exact frozen gate semantics and the limitation
  specific to the native unsplit RHS. A genuinely consumed split production
  source substep remains a possible interpretation requiring further evidence.
- `DESIGN_REVIEW.md`: finite-domain exact moments, normalization, constants,
  cutoff, coupling and scope checks.

The initial local-path reviews and an intentionally failed strict byte-binding
attempt are preserved. The failed binding concerned producer comment/scope
edits after an execution; the producer supplied hardened fresh runs with exact
snapshots, and the final independent review binds those bytes. Initial numerical
results remain historical and are not relabelled as the final executable.
Final assertion-bearing review scripts reject `-O` and a nonzero
`PYTHONOPTIMIZE` before creating any output directory. Their refusal checks are
recorded in `optimized-guard-refusals/refusal_receipt.json`.

Review code is GPL-3.0-only; `LICENSE.txt` contains the upstream GPLv3 license
text. Nudec attribution: baugid/Nudec_LLP_Solver, official commit
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`. No upstream implementation is
copied into this review; the mixing probe imports its source/mixing callables.
Every executed final review retains its own script bytes and reference module
where applicable. Output paths must be new.

Reproduce from this review directory with the pinned Python environment:

```sh
python -B review_domain_artifacts.py --upstream /path/to/pinned/nudec --domain /path/to/domain-bundle --output /new/path/domain-review
python -B review_runtime_artifacts.py --runtime-results /path/to/runtime-bundle/results-serialization-fix --output /new/path/runtime-review
python -B frozen_stepper_mixing_probe.py --upstream /path/to/pinned/nudec --output /new/path/mixing-review
```

Use Python 3.12.14, NumPy 2.3.5, SciPy 1.16.3, Numba 0.63.1 and llvmlite
0.46.0, disable bytecode writing, and set the BLAS/OpenMP/Numba thread limits
to one as in the producer runtime. The domain bundle must preserve its final
`results-hardened-declared-replay` and `results-hardened-phase-replay` paths.
Hashes establish byte identity, not physical correctness.

This review does not independently derive the peer's QED identity findings.
It does independently diagnose the unsplit source-mixing mismatch and records
the source quadrature failure. The unresolved conservation/cutoff/QED issues,
full source-window domain and history checks, production-stepper evidence,
transport refinements, six-process weak adapter and nuclear consumption remain
separate gates before any physical or observational interpretation.
