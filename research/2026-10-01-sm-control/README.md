# Reproducible unmodified PRIMAT Standard Model controls

Recorded 2026-10-01 in the project's America/Los_Angeles date convention
(machine timestamps are 2026-10-02 UTC).

Three documented Python-API Standard Model BBN controls ran successfully with
unmodified official [PRIMAT](https://github.com/CyrilPitrou/primat) source. They
establish a working upstream calculation for later integration checks. They are
**not DMDE predictions, independent physics replications, observational fits,
or evidence for a dark-matter/dark-energy mechanism**.

| Official source revision | Configuration | Yp (BBN mass fraction) | D/H | Neff |
| --- | --- | ---: | ---: | ---: |
| Current `4bf97d5082eee54b9df50d88f43182bb651fea80` (0.3.3) | small, default precision | 0.24699894798444227 | 2.435860013230952e-5 | 3.0439772985579183 |
| Current, same revision | large, amax=8, default precision | 0.24700235492652864 | 2.4365286436668656e-5 | 3.0439772985579183 |
| Historical `908028da9426370f2f41ca996503650eef34795a` (0.3.2) | small, default precision | 0.24699894798444227 | 2.435860013230952e-5 | 3.0439772985579183 |

The small-network runs use the README quick-start physics settings, with
`force_backend="python"`. The large, `amax=8` run uses the standard
`runfiles/primat_run.py` physics configuration through the same documented API.
The wrapper adds external output/cache paths and diagnostic exports. No upstream
file, nuclear rate table, release payload, or provider contract was modified.

## What was assumed and calculated

- Fixed cosmological input: Omega_b h^2 = 0.02242; DeltaNeff = 0. The standard
  upstream cosmological background is retained, including its default ordinary
  cold-dark-matter density. This is not a theory for that component.
- Fixed upstream neutron lifetime: 878.4 s. Standard incomplete neutrino
  decoupling, spectral distortions, radiative corrections, finite nucleon mass
  corrections, thermal corrections, and nuclear QED corrections are enabled.
- Relative ODE tolerance: 1e-7. Background temperature range: 40 to 0.001 MeV.
  Full requested and effective options are recorded separately in each run.
- No parameter was fitted to observations. No DMDE source, nonthermal muon-decay
  injection, custom neutrino spectrum, or transport-to-BBN bridge was supplied.
- **Shipped weak, thermal weak, plasma electron, and QED tables/caches were
  reused.** The background and nuclear ODE solve executed locally. This did
  not independently recalculate all weak-rate integrals or thermal corrections.
- Python 3.12.14, NumPy 2.3.5, SciPy 1.16.3, Linux x86_64. No Numba, Vegas, or
  compiled C backend was installed. The documented Python fallback suffices.
  Source import emits `v0.0.0+unknown` because distribution metadata is absent;
  the full Git revision and upstream `pyproject.toml` hash identify the source.
- One BLAS/OpenMP thread was requested. The logged successful solve times were
  about 1.57 s (current small), 6.19 s (current large), and 1.50 s (pinned small).

## Verification and limits

`verify_controls.py` validates the receipts and reference ranges, without
rerunning the solver or writing files by default. It prints its receipt to
stdout; the existing `verification.json` remains the original historical receipt.
It verifies file hashes, declared backend and settings,
nonnegative finite final abundances, baryon sums, the active abundance history,
background monotonicity, and the sum of background energy-density components.
Final baryon-number errors are about 1.65e-12, within the upstream 1e-10 bound.
The scalar outputs lie within the upstream numerical reference tolerances.
These tolerances are software regression bounds, not observational errors.

The first **64 of 500** abundance-export rows are all zero because they precede
the nuclear network start. This is documented zero padding in upstream
`primat/nuclear_network.py` (`_write_time_evolution`); it is not a physical
absence of baryons. Verification requires a contiguous leading zero prefix,
then checks conservation over every remaining row. Raw exports are preserved.
The large-run original `checks.json` left its baryon sum null because the first
wrapper's isotope map omitted He6; `verify_controls.py` independently computes
and checks its complete sum using all isotope masses, without changing outputs.

The historical source pin produces the same three scalars as current source in
this particular environment and cached/default configuration. This narrow
agreement is not a guarantee of equivalence for other options. The current
repository contains substantial changes since that pin.

The earlier public backend audit reported Yp = 0.24699183580343323 and
D/H = 2.435606846544578e-5. **Those exact scalar values were not reproduced.**
Compared with that note, this pinned run differs by about 7.1122e-6 in Yp and
2.5317e-9 in D/H, while Neff agrees. The older note does not specify complete
runtime settings, software, and cache provenance. The cause is undetermined;
neither historical evidence nor the frozen provider contracts were rewritten.
`verification.json` records the numerical differences.

Two initial local wrapper failures occurred *after* successful ODE solves:
serializing upstream `EvolutionResult`, then printing a NumPy boolean. The
wrapper was corrected with dataclass/NumPy serialization and the affected
control rerun; both failure logs are preserved in `failures/`. These were
recording failures, not failed BBN solutions. No scientific output was tuned.

No uncertainty Monte Carlo, fresh high-precision thermal-rate integration,
nonthermal high-energy endpoint test, full C/Python comparison, observational
likelihood, perturbation, structure-formation, lensing, or late-time expansion
calculation was performed. This control closes none of the frozen DMDE causal
evidence gates on its own.

## Reproduce

Each cloud task is already isolated. Use its existing checkout; do not create a
Git worktree unless the user explicitly requests one. Keep the official upstream
dependency cache distinct from the research repository and all outputs outside
the upstream checkout. Preserve user changes and require the dependency checkout
to be clean before changing its revision.

```bash
mkdir -p /workspace/shared/dmde-upstream
git clone https://github.com/CyrilPitrou/primat.git /workspace/shared/dmde-upstream/primat
python -m venv /workspace/shared/dmde-upstream/.venv
/workspace/shared/dmde-upstream/.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir numpy==2.3.5 scipy==1.16.3
git -C /workspace/shared/dmde-upstream/primat checkout --detach 4bf97d5082eee54b9df50d88f43182bb651fea80
```

Skip clone/venv creation when those existing locations are already valid. No
additional secret is required for this public dependency; normal HTTPS/TLS and
platform authentication were used. Required destinations are GitHub and PyPI's
package hosts (`github.com`, `pypi.org`, `files.pythonhosted.org`). Do not replace
an unknown network allowlist. Do not install a package merely named `primat`
without verifying its source and revision for this reproduction.

Run the small control with a new output directory (the wrapper refuses to
overwrite an existing one):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /workspace/shared/dmde-upstream/.venv/bin/python \
  /workspace/dmde-research/research/2026-10-01-sm-control/run_primat_sm_control.py \
  --source /workspace/shared/dmde-upstream/primat \
  --output /workspace/shared/dmde-upstream/results/reproduction-current-small
```

For the documented large control add `--network large --amax 8`, choosing a
different output path. For the historical small control, while no solver is
running, check out `908028da9426370f2f41ca996503650eef34795a` in the dependency
cache, run with a distinct path, then restore the exact current revision above.
The wrapper hashes all tracked source/data files, checks clean Git status before
and after, exports effective settings and results, and saves its own source.
The `cache_dir` overlay may read shipped upstream caches but redirects writes.
The environment was left at current revision `4bf97d5`, clean, with no process
required to remain running. Saved receipts include logs and runner snapshots.

Verify the committed receipts:

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/shared/dmde-upstream/.venv/bin/python \
  /workspace/dmde-research/research/2026-10-01-sm-control/verify_controls.py
```

To retain a fresh verification receipt, append `--output PATH`, using a new file
outside the checkout (or an existing ignored output directory). The parent
directory must exist. The verifier refuses to overwrite an existing file and
never updates the historical receipt implicitly.

## Provenance and publication scope

Only public official upstream material and newly executed calculations were
used. No private archive file or personal document was copied into this record.
PRIMAT is Copyright 2026 Cyril Pitrou and Julien Froustey, licensed under
GPL-3.0-or-later; its license is retained in the separate dependency checkout.
This folder records outputs, checksums and original external wrapper code;
it does not vendor PRIMAT source or rate datasets. Public scientific controls
may support an integration-status update, but this small numerical control
does not warrant a DMDE discovery claim or a new physics Zenodo release.
