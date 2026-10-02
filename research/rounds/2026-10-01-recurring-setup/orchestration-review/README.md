# Recurring-control orchestration review

This separate-agent review ran on 2 October 2026 UTC. All 11 mocked checks
passed for the driver hash recorded in `REVIEW_RECEIPT.json`. It checks the
maintenance driver's failure handling, output containment, concurrency guard,
and historical-review semantics. It is not external peer review or an
independent calculation of the scientific results.

Every case uses a fresh temporary checkout root under `/tmp`. Subprocesses,
dependency metadata, and scientific verification calls are mocked. No solver,
scientific control, private input, credential, network service, or repository
write is involved. Temporary case outputs are deleted after inspection.

The checks cover missing dependency metadata, initial and final source-snapshot
errors, subprocess timeout, nonzero exit, subprocess-start error, generated and
nested symlink escapes, concurrent local invocation, changed documentation
versus changed numerical sources, and manifest path traversal. Failure receipts
retain the actual cause and artifact hashes; timed-out attempts are recorded.
Changed authored documents are identified as outside the historical review
without blocking unchanged numerical sources.

The workflow was also inspected: it runs ordinary pull-request, scheduled, or
manual public maintenance with read-only repository permissions; it does not
consume private inputs or invoke a model. Its upload scope is one new public
run/attempt dossier, with 14-day retention. This inspection does not prove a
GitHub-hosted run completed or that the recurring schedule is active.

Reproduce with Python 3.10+ on Linux, using an existing absent output path:

```bash
python3 -B review_controls.py \
  --driver /path/to/dmde-research/scripts/run_research_round.py \
  --output /tmp/dmde-recurring-review-new.json
```

The script needs only Python's standard library, refuses receipt overwrites,
records both source hashes, and returns nonzero if any reviewed behavior fails.
`ARTIFACT_SHA256.json` hashes this authored dossier; it excludes itself.
