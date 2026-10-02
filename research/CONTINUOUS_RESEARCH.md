# Recurring DMDE work — 1 October 2026

Ricardo authorizes continued DMDE investigation and appropriate GitHub updates.
His requested model is GPT-6.1 Sol with Ultra reasoning. These are operating
preferences, not a claim that a scheduler or model session is currently active.
HDBLAST remains a separate project. Research hypotheses are not required to
produce positive results or a breakthrough.

## What is implemented

`scripts/run_research_round.py` runs the existing public numerical controls into
a new directory below `generated/`: release integrity, both payloads, pair
geometry, 13 equilibrium tests, equilibrium report, separate adaptive integration
and comparison, and checks of the three saved Standard Model control dossiers.
It records source/runtime identity, per-step logs, timestamps, status and output
hashes; preserves failed checks; refuses overwrites and concurrent local rounds;
and checks that tracked files were unchanged. No new transport or nuclear-network
solve is performed by this maintenance script. A pass is a reproduction result.
Historical numerical-source and dossier hashes remain strict. Later documentation
changes are recorded separately: the old documentation review does not cover
changed text, while a new scientific conclusion still requires its own review.
The [setup verification dossier](rounds/2026-10-01-recurring-setup/README.md)
preserves the clean-commit replay, raw public outputs and 11 mocked orchestration
checks. It does not establish GitHub-hosted execution or an active AI scheduler.

From the repository root, using an environment with NumPy 2.3.5 and SciPy 1.16.3:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B scripts/run_research_round.py \
  --output-dir generated/rounds/choose-a-new-round-id
```

The GitHub Actions workflow requests this maintenance check every six hours at
00:17, 06:17, 12:17 and 18:17 UTC, plus on relevant pull-request changes and manual
dispatch. It uses read-only repository permissions and uploads only its newly
generated public dossier, with 14-day artifact retention. It does not access the
private archive, invoke an AI model, merge changes, deploy a website or publish
Zenodo versions. GitHub logs and these artifacts are public.

Scheduled workflows use the default branch. The workflow must be merged and
Actions enabled before its recurring schedule can run. GitHub can delay scheduled
jobs; public-repository schedules may be disabled after 60 days without activity.
Successful cloud replay does not prove GitHub-hosted execution. Inspect Actions
run status before claiming the scheduler is active. A schedule in source is not
evidence of a completed scheduled run.

## What full AI research requires

No callable scheduler for launching new AI research sessions is connected to
this chat. An ephemeral cloud session cannot guarantee 24/7 execution. A persistent
Codex automation or other authorized agent runner must launch the prompt in
[RESEARCH_ROUND_PROMPT.md](RESEARCH_ROUND_PROMPT.md), selecting GPT-6.1 Sol and
Ultra in that runner when supported. Verify the model and runner there; the
maintenance cron does not select or start either. No API key is needed for the
maintenance workflow. No new secret requirement has been added.

Use a six-hour launch cadence as an initial recommendation, one active AI round
at a time, with a finite execution budget set in the runner. End each invocation
at a reviewable checkpoint or a documented blocker. Persist the next question
before ending. The scheduler launches the next invocation; a chat cannot relaunch
itself merely by containing an instruction to continue forever. Do not create
unbounded recursive sessions or fabricate progress to fill the schedule.

## Scientific round protocol

1. Read current Git refs, open PRs, [CLAIM_LEDGER.md](CLAIM_LEDGER.md),
   [NEXT_TESTS.md](NEXT_TESTS.md), [ROUND_QUEUE.json](ROUND_QUEUE.json), and the
   last substantive round. Historical attachments and handoffs are references;
   verify them against current source.
2. Select one unresolved question whose prerequisites are available. Write its
   assumptions, fixed inputs, acceptance thresholds, predictions and negative
   controls before calculation. Do not claim retrospective preregistration.
3. Execute a falsifiable test. Record exact commands, source and input hashes,
   settings, dependencies, raw numerical outputs, failed attempts and uncertainty.
   State whether occupations were prescribed or actually evolved.
4. Use a separate reviewer for a substantive equation or numerical result. Review
   code and raw outputs; documentation review alone is not replication or peer
   review. Preserve disputed results rather than silently replacing them.
5. Publish explicitly selected, reviewed public files through the existing PR
   workflow. Keep private source inspection and personal documents private. Do
   not stage a workspace or copy raw archive inputs into public artifacts. Update
   claims and website wording only to the degree supported by the result.
6. Record the completed or blocked question, result class, falsification outcome,
   unresolved uncertainty and next gate. Repeated input/source fingerprints are
   reproductions, not additional scientific findings. If blocked, move to a
   distinct executable question or report the required access once.

Each substantive round gets a unique dossier under `research/rounds/` after
review; provisional outputs stay in ignored `generated/`. Record separately:
assumptions, fitted parameters, predictions, evidence and interpretation limits.
The round queue starts with unexecuted items. Never mark them complete because
a protocol or a passing maintenance replay exists.

Compare specified mechanisms against conservation, expansion, BBN/CMB, growth,
structure and lensing, using matched established controls and dated primary
sources. Literature is an input to tests, not validation of this hypothesis.
The current dust-parent/radiation-daughter sector alone cannot cause acceleration
in ordinary GR. Missing dark-energy or microscopic equations remain missing.

Keep v0.9.20 frozen. A six-process production contract must be separately
versioned. Zenodo publication follows the existing reviewed release workflow;
do not publish a new version solely because another scheduled check passed.
Unavailable Mac/iCloud files and unavailable connected services must be named
as unavailable, not assumed inspected.
