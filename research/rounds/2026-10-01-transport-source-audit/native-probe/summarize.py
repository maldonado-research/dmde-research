#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Derive review tables from preserved native output; never calls native physics."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.dont_write_bytecode = True
BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "results-2026-10-01"


def write_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


rows = []
for domain in ("clipped", "complete"):
    for n in (65, 129, 257, 513, 1025):
        if not (BASE / f"emission_{domain}_n{n}" / "result.json").is_file():
            continue
        result = json.loads((BASE / f"emission_{domain}_n{n}" / "result.json").read_text())
        for flavor, i in [("electron", 0), ("muon", 1)]:
            row = {"domain": domain, "n": n, "flavor": flavor,
                   "native_number": result["native_number"][i],
                   "exact_retained_number": result["exact_retained"]["number"][i],
                   "native_energy_MeV": result["native_energy_MeV"][i],
                   "exact_retained_energy_MeV": result["exact_retained"]["energy_MeV"][i]}
            for name, numerical, exact in [
                ("number", result["native_number"][i], result["exact_full"]["number"][i]),
                ("energy", result["native_energy_MeV"][i], result["exact_full"]["energy_MeV"][i]),
                *[(f"p{k}", result["native_higher_p_moments_MeV_to_k"][str(k)][i],
                   result["exact_full"]["higher_p_moments_MeV_to_k"][str(k)][i]) for k in range(2, 6)],
            ]:
                row[f"{name}_fraction_of_full"] = numerical / exact
                row[f"{name}_relative_deficiency"] = (exact - numerical) / exact
            rows.append(row)
if rows:
    with (BASE / "emission_moment_summary.csv").open("x") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

rhs = json.loads((BASE / "rhs_n21" / "result.json").read_text())
weighted_sources = {}
branches = [rhs["configuration"]["rhs_native_branching_muon"], *rhs["configuration"]["rhs_other_branchings"]]
for tag in ("zero_on", "positive_on"):
    sources = rhs["runs"][tag]["sources"]
    combined = np.zeros((21, 3))
    for source in sources:
        samples = np.loadtxt(BASE / "rhs_n21" / source["file"], delimiter=",", skiprows=1)
        combined += branches[source["index"]] * samples[:, 2:]
    path = f"branch_weighted_preosc_{tag}.csv"
    with (BASE / "rhs_n21" / path).open("x") as handle:
        np.savetxt(handle, np.column_stack((samples[:, :2], combined)), delimiter=",",
                   header="q,p_MeV,branch_weighted_phi_e,branch_weighted_phi_mu,branch_weighted_phi_tau", comments="")
    weighted_sources[tag] = {
        "file": path, "phi_tau_exactly_zero": bool(np.all(combined[:, 2] == 0.0)),
        "finite": bool(np.isfinite(combined).all()),
        "scope": "Branch-weighted raw emission functions, before common LLP/time/Hubble amplitude and oscillations. Zero-count case has a nonzero shape but its native physical amplitude is zero.",
    }
write_json(BASE / "branch_weighted_preosc_summary.json", weighted_sources)
if "following SingleShot/Core interface" in rhs["branching_scope"]:
    write_json(BASE / "metadata_erratum.json", {
    "affected_file": "rhs_n21/result.json", "affected_field": "branching_scope",
    "original_text": rhs["branching_scope"],
    "correction": "The native branch0.4 is an externally predeclared fixture input. SingleShot passes its llp_muonBranching input unchanged, and LLP_parameters.py describes it as average primary muons. No native0.8-to0.4 conversion occurs; multiplicity0.8 is an external label, not a validated mapping.",
    "numerical_effect": "None: recorded native branch input was0.4 throughout.",
    "preservation": "The raw result metadata is preserved; native_probe.py wording was corrected after execution.",
    })

write_json(BASE / "artifact_sha256.json", {
    str(path.relative_to(BASE)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(BASE.rglob("*")) if path.is_file()
})
print(json.dumps({"derived_rows": len(rows), "weighted_source_tau_zero": all(x["phi_tau_exactly_zero"] for x in weighted_sources.values()),
                  "raw_outputs_preserved": True, "metadata_erratum_recorded": (BASE / "metadata_erratum.json").is_file()}))
