# Independent computational review

[AUDIT.md](AUDIT.md) states the reviewed claims, independent calculations and
validity limits. This is a separate-agent numerical review, not external peer
review or a DMDE model prediction. All inputs are public source code or newly
generated reference calculations; no private archive input is included.

The independent integrator uses SciPy adaptive quadrature in electron energy.
The producer uses NumPy Gauss–Legendre quadrature with different variables and
endpoint substitutions. The comparison covers all 13 declared temperatures,
including 0.25 MeV. The original receipts are preserved; running the scripts
prints fresh results and does not overwrite them.

## Reproduce

Dependencies for the recorded independent calculation: Python 3.12.14,
NumPy 2.3.5, SciPy 1.17.0. Use an existing matching environment, or install those
packages into an isolated virtual environment outside the repository. From the
repository root after this review directory is published:

```bash
PYTHONDONTWRITEBYTECODE=1 python research/2026-10-01-independent-review/independent_rates.py
PYTHONDONTWRITEBYTECODE=1 python research/2026-10-01-independent-review/compare_with_producer.py \
  --producer-dir research/2026-10-01-equilibrium-audit
```

To retain new outputs outside the published folder, use new paths:

```bash
PYTHONDONTWRITEBYTECODE=1 python research/2026-10-01-independent-review/independent_rates.py \
  --output /tmp/dmde-independent-rates-new.json
PYTHONDONTWRITEBYTECODE=1 python research/2026-10-01-independent-review/compare_with_producer.py \
  --producer-dir research/2026-10-01-equilibrium-audit \
  --output /tmp/dmde-producer-comparison-new.json
```

Both scripts refuse to overwrite an existing output file. Choose another path
if it already exists; a parent output directory must exist. The scripts do not
write into either research dossier implicitly. No network or credentials are
needed to rerun the calculations with the dependencies installed.

`independent_rates.json` and `producer_comparison.json` retain the original
audit results. A new comparison receipt also records the currently executed
source hashes and package versions. The original control artifact checks are
in `control_artifact_checks.json`; control verification is documented in the
[SM control dossier](../2026-10-01-sm-control/README.md).
