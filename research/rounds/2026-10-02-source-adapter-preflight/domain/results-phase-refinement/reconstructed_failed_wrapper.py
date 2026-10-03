#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Endpoint-phase sweep using the independently authored frozen callback."""
import argparse
import importlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

from source_grid_diagnostic import ME, MMU, exact_moments, frozen_michel, sha, source_receipt, write_json, independent_simpson

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--predeclaration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Fresh output directory required.")
    args.output.mkdir(parents=True)
    cfg = json.loads(args.predeclaration.read_text())
    before = source_receipt(args.upstream)
    write_json(args.output / "source_before.json", before)
    sys.path.insert(0, str(args.upstream.resolve()))
    constants = importlib.import_module("Constants")
    assert constants.me == ME and constants.mmu == 105.7
    grid = importlib.import_module("Momentum_Grid")
    moments = exact_moments()
    xs = np.linspace(cfg["x_scan"]["min"], cfg["x_scan"]["max"], cfg["x_scan"]["count"])
    rows = []
    arrays = {"x_scan": xs}
    for n in cfg["native_n_ladder"]:
        grid.setupGrid(cfg["q_max"], n, cfg["q_min"])
        err = np.empty((len(xs), 2, 6))
        for ti, x in enumerate(xs):
            p = grid.gridVals * ME / x
            actual = frozen_michel(p, x, {"mu": 1.})
            powers = np.vstack([p ** k for k in range(6)])
            values = (actual[:2] * (ME / x * grid.gridWeights)) @ powers.T
            err[ti] = values / moments - 1
        flat = np.unravel_index(np.argmax(np.abs(err)), err.shape)
        simpson = independent_simpson(grid.gridVals)
        rows.append({"n": n, "max_moment_relative_error": float(np.max(np.abs(err))),
                     "worst_x": float(xs[flat[0]]), "worst_flavor": ("electron", "muon")[flat[1]], "worst_k": flat[2],
                     "all_scanned_rows_k0_to_k5_pass": bool(np.max(np.abs(err)) <= cfg["moment_relative_ceiling"]),
                     "relative_native_weight_error_max": float(np.max(np.abs(grid.gridWeights / simpson - 1))),
                     "dq": float(grid.gridVals[1] - grid.gridVals[0]), "estimated_collision_work_vs_301": (n / 301) ** 3})
        arrays[f"n{n}_relative_moment_errors"] = err
    qstar0 = cfg["x_scan"]["min"] * MMU / (2 * ME)
    full_qmax = 16.993868549367075 * MMU / (2 * ME)
    # Leading discontinuity term: Simpson endpoint phase is at most 2h/3;
    # the dimensionless muon density is F_mu(1)=2 and M_mu,5=11/36.
    coefficient = 4 / (3 * (11 / 36))
    dq_allow = cfg["moment_relative_ceiling"] * qstar0 / coefficient
    estimated_n = int(np.ceil((full_qmax - cfg["q_min"]) / dq_allow)) + 1
    if estimated_n % 2 == 0:
        estimated_n += 1
    write_json(args.output / "results.json", {"rows": rows, "scope": cfg["scope"],
               "leading_endpoint_error_estimate": {"formula": "max_relative_muon_k5 ~ (48/11)*dq/q_star_initial",
               "coefficient": coefficient, "q_star_initial": qstar0, "dq_allow_for_005": dq_allow,
               "full_reference_cap_qmax": full_qmax, "estimated_odd_full_cap_n": estimated_n,
               "estimated_collision_work_vs_301": (estimated_n / 301) ** 3,
               "warning": "asymptotic phase estimate, not rigorous error bound or achieved convergence; native weight construction also needs conditioning review at this N"},
               "execution": {"python": platform.python_version(), "numpy": np.__version__, "wrapper_sha256": sha(__file__),
               "callback_module_sha256": sha(Path(__file__).with_name("source_grid_diagnostic.py")), "predeclaration_sha256": sha(args.predeclaration),
               "private_inputs": False, "native_constant_overrides": False, "native_collision_execution": False}})
    np.savez_compressed(args.output / "raw_phase_scan.npz", **arrays)
    after = source_receipt(args.upstream)
    assert before == after
    write_json(args.output / "source_after.json", after)
    write_json(args.output / "artifact_sha256.json", {p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file()})
    print(json.dumps(rows, allow_nan=False))


if __name__ == "__main__":
    main()
