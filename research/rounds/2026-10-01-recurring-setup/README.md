# Recurring-round setup verification — 1 October 2026

This dossier records an actual cloud replay of the public numerical-maintenance
routine and a separate agent review of its orchestration. It is a software setup
checkpoint, with no new transport/BBN prediction or discovery. AI assistance was
used; planning and review agents were configured as GPT-6.1 Sol with Ultra reasoning.
The separate review is not external peer review.

`public-replay/` preserves all eight step logs, numerical outputs, runtime/source
identity and SHA-256 manifest from a clean committed checkout. The receipt records
the exact executed source commit and driver hash. Output paths retain their original
`generated/` locations; these published files are byte-identical copies. Repeating
existing numerical inputs is a reproduction, not additional scientific evidence.

`orchestration-review/` supplies a reproducible script and 11 passing mocked checks.
They use temporary roots and mocked subprocesses, and execute no scientific solver.
The review exposed and fixed documentation-provenance handling, failure-receipt
retention, attempted-step recording and symlink containment. Actual guard checks
also refused overwrites, outside output paths, optimized Python and concurrent runs.

`VALIDATION.json` states the setup scope. GitHub-hosted execution remains unverified;
the default-branch workflow must be activated and its run status checked. There is
no connected AI scheduler. No private archive, attachment, personal document,
credential or new observational dataset is included.

From the repository root, reproduce the orchestration review without overwriting
its historical receipt:

```bash
python3 research/rounds/2026-10-01-recurring-setup/orchestration-review/review_controls.py \
  --driver scripts/run_research_round.py \
  --output generated/rounds/choose-a-new-review-id.json
```

Use `research/CONTINUOUS_RESEARCH.md` for the numerical round command, activation
requirements and the protocol for substantive future research.
