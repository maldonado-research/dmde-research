#!/usr/bin/env python3
"""Verify saved PRIMAT receipts; print to stdout, with optional new output file."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, help="Write a new JSON receipt to this path; existing files are never overwritten.")
args = parser.parse_args()
if args.output is not None and args.output.exists():
    parser.error(f"Refusing to overwrite existing output: {args.output}")

ROOT = Path(__file__).resolve().parent
RUNS = ["current-4bf97d5-sm-small", "current-4bf97d5-sm-large-amax8", "pinned-908028d-sm-small"]
CURRENT = "4bf97d5082eee54b9df50d88f43182bb651fea80"
PINNED = "908028da9426370f2f41ca996503650eef34795a"

def read(path):
    return json.loads(path.read_text())

def A(name):
    if name in {"n", "p"}:
        return 1
    match = re.fullmatch(r"[A-Z][a-z]?(\d+)", name)
    if not match:
        raise ValueError(f"Unknown isotope name: {name}")
    return int(match.group(1))

summary = {"scope": "Checks of saved upstream SM control artifacts; no DMDE prediction or independent physics replication.", "runs": {}}
for label in RUNS:
    run = ROOT / "runs" / label
    for name, expected in read(run / "output_sha256.json").items():
        actual = hashlib.sha256((run / name).read_bytes()).hexdigest()
        assert actual == expected, (label, name, "checksum mismatch")
    result = read(run / "results.json")
    provenance = read(run / "provenance.json")
    settings = read(run / "effective_settings.json")
    assert provenance["source_commit"] == (PINNED if label.startswith("pinned") else CURRENT)
    assert provenance["backend"] == "python"
    assert provenance["runner_sha256"] == hashlib.sha256((run / "runner_snapshot.py").read_bytes()).hexdigest()
    assert settings["Omegabh2"] == 0.02242 and settings["DeltaNeff"] == 0
    # Upstream renamed this option between the historical and current pins.
    jit_flag = "use_numba" if "use_numba" in settings else "numba_installed"
    assert settings[jit_flag] is False
    assert read(run / "checks.json")["source_clean"] is True
    final_baryon_error = abs(sum(A(k) * v for k, v in result["Y_final"].items()) - 1)
    assert final_baryon_error < 1e-10
    assert all(np.isfinite(v) and v >= 0 for v in result["Y_final"].values())
    evolution = np.loadtxt(run / "abundance_evolution.tsv", skiprows=1)
    names = (run / "abundance_evolution.tsv").read_text().splitlines()[0].split("\t")
    weights = np.array([A(k[2:]) for k in names[6:]])
    baryon_sum = evolution[:, 6:] @ weights
    active = np.flatnonzero(baryon_sum > 0)
    first = int(active[0])
    # PRIMAT pads only the leading pre-nuclear part of the background grid
    # with zeros. Require that exact prefix, rather than dropping arbitrary
    # zero rows that might hide a failure inside the physical solution.
    assert np.all(evolution[:first, 6:] == 0)
    assert np.array_equal(active, np.arange(first, len(evolution)))
    evolution_baryon_error = float(np.max(np.abs(baryon_sum[first:] - 1)))
    assert evolution_baryon_error < 1e-10
    assert np.isfinite(evolution).all() and np.min(evolution[:, 6:]) >= 0
    background = np.loadtxt(run / "background_evolution.tsv", skiprows=1)
    assert np.isfinite(background).all()
    assert np.all(np.diff(background[:, 0]) < 0)  # temperature decreases
    assert np.all(np.diff(background[:, 1]) > 0)  # cosmic time increases
    assert np.all(np.diff(background[:, 2]) > 0)  # scale factor increases
    assert np.all(background[:, 3] > 0)
    density_error = float(np.max(np.abs(background[:, -1] - background[:, 8:11].sum(axis=1)) / background[:, -1]))
    assert density_error < 1e-14
    # Published upstream reference bounds, not observational likelihoods.
    if settings["network"] == "small":
        assert abs(result["YPBBN"] - 0.24699896) < 1e-5
        assert abs(result["DoH"] - 2.4358605e-5) < 3e-9
    else:
        assert abs(result["YPBBN"] - 0.24700179) < 1e-5
        assert abs(result["DoH"] - 2.4366098e-5) < 2e-8
    assert abs(result["Neff"] - 3.0439772986) < 1e-5
    summary["runs"][label] = {
        "YPBBN": result["YPBBN"], "DoH": result["DoH"], "Neff": result["Neff"],
        "final_baryon_abs_error": final_baryon_error,
        "post_start_evolution_baryon_abs_error": evolution_baryon_error,
        "leading_pre_nuclear_zero_rows": first,
        "first_nuclear_sample_T_MeV": float(evolution[first, 2]),
        "background_component_density_sum_max_rel_error": density_error,
        "checks_pass": True,
    }
old_note = {"YPBBN": 0.24699183580343323, "DoH": 2.435606846544578e-5, "Neff": 3.0439772985579183}
pinned = summary["runs"]["pinned-908028d-sm-small"]
summary["historical_note_discrepancy"] = {
    "source": "provider/docs/DMDE_v0920_PUBLIC_BACKEND_INTEGRATION_AUDIT.md",
    "old_note_scalars": old_note,
    "new_pinned_minus_old_note": {key: pinned[key] - old_note[key] for key in old_note},
    "relative_difference": {key: (pinned[key] - old_note[key]) / old_note[key] for key in old_note},
    "explanation": "Original note omits full runtime settings/software/cache provenance. Cause remains undetermined; exact reproduction of its scalar receipt has not been established.",
}
receipt = json.dumps(summary, indent=2, sort_keys=True)
if args.output is not None:
    with args.output.open("x") as handle:
        handle.write(receipt + "\n")
print(receipt)
