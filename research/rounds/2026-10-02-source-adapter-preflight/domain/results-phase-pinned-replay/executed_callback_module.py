#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Independent public-source diagnostic; upstream files remain untouched.

Uses the official baugid/Nudec_LLP_Solver native grid and a source-specific exact-muon-mass callback.
Every native mass remains unchanged. Analytic expected arrays and conservation diagnostics are
independently written here. No native collision or transport solve is run.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.special import expit

sys.dont_write_bytecode = True
SPECIES = ("nue", "nuebar", "numu", "numubar", "nutau", "nutaubar")
EXPECTED_COMMIT = "0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62"
ME = 0.5109989
FROZEN_WEAK_ME = 0.51099895
MMU = 105.6583755


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def source_receipt(upstream):
    files = subprocess.check_output(["git", "-C", str(upstream), "ls-files", "-z"]).decode().split("\0")
    return {"commit": subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip(),
            "status_porcelain": subprocess.check_output(["git", "-C", str(upstream), "status", "--porcelain=v1"], text=True),
            "tracked_sha256": {name: sha(upstream / name) for name in files if name}}


def consumer_map(upstream):
    rows = []
    for path in sorted(upstream.rglob("*.py")):
        tree = ast.parse(path.read_text())
        imports_constants = any(isinstance(node, ast.ImportFrom) and node.module == "Constants" for node in ast.walk(tree))
        references = {key: sorted({node.lineno for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == key and isinstance(node.ctx, ast.Load)}) for key in ("me", "mmu")}
        if imports_constants or path.name == "Constants.py":
            rows.append({"file": str(path.relative_to(upstream)), "wildcard_constant_import": imports_constants,
                         "mass_load_lines": references, "override": "none; native copied masses retained, source callback consumes only its exact MMU"})
    return rows


def frozen_k(p):
    """Independent dimensionless Michel-polynomial convention with hard support."""
    u = 2 * p / MMU
    support = (p >= 0) & (p <= MMU / 2)
    fe = np.where(support, 12 * u * u * (1 - u), 0.)
    fm = np.where(support, 2 * u * u * (3 - 2 * u), 0.)
    return (2 / MMU) * np.stack((fe, fm, np.zeros_like(fe)))


def frozen_michel(p, x, decay_probabilities):
    """Catalog callback in native K(p)=dN/dp units; exact source m_mu only.

    This independently authored callback is the intended source prescription,
    not an override of transport/EOS/collision constants.
    """
    result = np.zeros((3, len(p)))
    active = (p >= 0) & (p <= MMU / 2)
    momenta = p[active]
    result[0, active] = 96 * momenta ** 2 * (1 - 2 * momenta / MMU) / MMU ** 3
    result[1, active] = 48 * momenta ** 2 * (1 - 4 * momenta / (3 * MMU)) / MMU ** 3
    return float(decay_probabilities["mu"]) * result


def exact_moments():
    return np.array([[(MMU / 2) ** k * 12 / ((k + 3) * (k + 4)) for k in range(6)],
                     [(MMU / 2) ** k * 2 * (k + 6) / ((k + 3) * (k + 4)) for k in range(6)]])


def independent_simpson(q):
    h = (q[-1] - q[0]) / (len(q) - 1)
    weights = np.full(len(q), 2 * h / 3)
    weights[1:-1:2] = 4 * h / 3
    weights[[0, -1]] = h / 3
    return weights


def projection_geometry(q):
    """All triples for a small grid; native search/nearest rule independently coded."""
    i, j, k = np.meshgrid(q, q, q, indexing="ij")
    lp = (i + j - k).ravel()
    lp = lp[(lp >= q[0]) & (lp <= q[-1])]
    upper = np.clip(np.searchsorted(q, lp), 0, len(q) - 1)
    lower = np.clip(upper - 1, 0, len(q) - 1)
    pick = np.where(q[upper] - lp > lp - q[lower], lower, upper)
    defect = q[pick] - lp
    return {"valid_triples": int(len(lp)), "max_absolute_l_defect": float(np.max(np.abs(defect))),
            "nonzero_above_roundoff_count": int(np.count_nonzero(np.abs(defect) > 1e-12)),
            "rms_l_defect": float(np.sqrt(np.mean(defect * defect)))}


def row_summary(grid, distribution, x, label):
    c = ME / x
    p = grid.gridVals * c
    actual = distribution(p, x, {"mu": 1., "pi": 1.})
    expected = frozen_k(p)
    measured = np.array([[np.sum(grid.gridWeights * c * p ** k * actual[a]) for k in range(6)] for a in range(2)])
    moments = exact_moments()
    relative = measured / moments - 1
    peak = np.max(np.abs(actual[:2] - expected[:2])) / np.max(expected[:2])
    return {"case": label, "n": int(grid.n), "x": x, "q_min": float(grid.gridVals[0]),
            "q_max": float(grid.gridVals[-1]), "dq": float(grid.gridVals[1] - grid.gridVals[0]),
            "q_star": x * MMU / (2 * ME), "p_min": float(p[0]), "p_max": float(p[-1]),
            "source_support_nodes": int(np.count_nonzero(p <= MMU / 2)),
            "endpoint_complete": bool(p[-1] >= MMU / 2), "moments": measured.tolist(),
            "moment_relative_error": relative.tolist(), "max_moment_relative_error": float(np.max(np.abs(relative))),
            "all_k0_to_k5_within_005": bool(np.max(np.abs(relative)) <= .005),
            "node_peak_scaled_shape_error": float(peak),
            "finite_nonnegative": bool(np.isfinite(actual).all() and (actual >= 0).all()),
            "above_endpoint_max": float(np.max(actual[:, p > MMU / 2], initial=0))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--predeclaration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise SystemExit("Use a fresh output directory; historical negatives must be preserved.")
    out.mkdir(parents=True)
    cfg = json.loads(args.predeclaration.read_text())
    before = source_receipt(args.upstream)
    if before["commit"] != EXPECTED_COMMIT or before["status_porcelain"]:
        raise SystemExit("Expected clean pinned upstream source.")
    write_json(out / "source_before.json", before)
    public_inputs = [args.predeclaration.resolve(), Path(__file__).resolve()]
    write_json(out / "execution_identity.json", {"executed_wrapper_sha256": sha(__file__), "predeclaration_sha256": sha(args.predeclaration),
               "python": platform.python_version(), "numpy": np.__version__, "public_inputs": [str(x) for x in public_inputs],
               "private_inputs": False, "scope": cfg["scope"]})

    sys.path.insert(0, str(args.upstream.resolve()))
    native_constants = importlib.import_module("Constants")
    native = {"me": native_constants.me, "mmu": native_constants.mmu}
    # No global mass override: the callback alone owns the exact frozen m_mu.
    grid = importlib.import_module("Momentum_Grid")
    distributions = importlib.import_module("Distributions")
    distributions.getDistribution = [frozen_michel]
    modules = [native_constants, distributions]
    for name in ("Thermodynamics.Thermodynamics_ideal_gas", "Thermodynamics.Thermal_QED_corrections", "Collision_term.Collision_term_diagonal", "System_Nudecoupling", "Core"):
        modules.append(importlib.import_module(name))
    mass_overrides = [{"module": module.__name__, "me": getattr(module, "me", None), "mmu": getattr(module, "mmu", None)} for module in modules]
    assert all(item["me"] == native["me"] and item["mmu"] == native["mmu"] for item in mass_overrides)
    collision = importlib.import_module("Collision_term.Collision_term_diagonal").Collision_term_diagonal
    assert not collision.signatures  # neither thermal/native collision runtime is exercised
    expected_pion = (distributions.mpi ** 2 - native["mmu"] ** 2) / (2 * distributions.mpi)
    assert distributions.__pion_neutrino_energy == expected_pion
    write_json(out / "consumer_override_map.json", {"native_mass_defaults_MeV": native, "mass_roles": {"transport_me": ME, "source_callback_mmu": MMU, "frozen_weak_kernel_me_unused_here": FROZEN_WEAK_ME}, "global_mass_overrides": False, "source_catalog": ["source_grid_diagnostic.frozen_michel"], "branches": "[2*B_mumu]",
               "imported_consumers": mass_overrides, "static_all_consumers": consumer_map(args.upstream),
               "excluded_entrypoints": ["SingleShot.py and BatchLauncher.py are never imported: executing entrypoints is outside this diagnostic"],
               "derived_pion_energy_MeV": expected_pion, "collision_jit_signatures": [str(x) for x in collision.signatures]})

    qmax = cfg["x_cap_reference_only"] * MMU / (2 * ME)
    rows = []
    weight_checks = []
    for n in cfg["native_n_ladder"]:
        grid.setupGrid(qmax, n, cfg["q_min"])
        alternate = independent_simpson(grid.gridVals)
        weight_checks.append({"n": n, "all_native_weights_positive": bool(np.all(grid.gridWeights > 0)),
                              "max_native_vs_analytic_simpson_absolute": float(np.max(np.abs(grid.gridWeights - alternate))),
                              "max_native_vs_analytic_simpson_relative": float(np.max(np.abs(grid.gridWeights / alternate - 1))),
                              "relative_weight_sum_error": float(np.sum(grid.gridWeights) / (qmax - cfg["q_min"]) - 1)})
        for x in cfg["x_probes"]:
            rows.append(row_summary(grid, frozen_michel, x, "full_reference_cap_native_weights"))
    # Original formula remains deliberately clipped.
    grid.setupGrid(cfg["x_cap_reference_only"] * MMU / 2, 3001, cfg["q_min"])
    rows.append(row_summary(grid, frozen_michel, cfg["x_cap_reference_only"], "original_domain_formula_negative"))
    # Shape mismatch from the original rounded mass is preserved on the same frozen nodes.
    grid.setupGrid(qmax, 3001, cfg["q_min"])
    rows.append(row_summary(grid, distributions.muonDistribution, 1., "native_rounded_muon_mass_negative"))
    # Endpoint below q_max: native full-domain Simpson weights over a source discontinuity.
    endpoint_rows = []
    for n in (301, 1001, 3001):
        grid.setupGrid(40., n, cfg["q_min"])
        for x in (.1, .15, .2):
            endpoint_rows.append(row_summary(grid, frozen_michel, x, "short_window_native_weights"))

    grid.setupGrid(qmax, cfg["array_grid_n"], cfg["q_min"])
    q, w = grid.gridVals.copy(), grid.gridWeights.copy()
    time_y = np.array(cfg["diagnostic_t_over_tau"])
    tau = cfg["diagnostic_test_card"]["tau_s"]
    times = time_y * tau
    xs = np.full(len(times), cfg["x_initial"])
    cs = ME / xs
    tstart = 1.00003 * ME / cfg["x_initial"]
    s0 = (2 * np.pi ** 2 / 45) * 10.75 * tstart ** 3
    sref = s0 * (cfg["x_initial"] / xs) ** 3
    f = expit(-q / 1.00003)
    occupation = np.broadcast_to(f, (len(times), len(q))).copy()
    states3, sources3, expected3 = [], [], []
    for time, x, c, sr in zip(times, xs, cs, sref):
        p = c * q
        active = 0 <= time < 18 * tau
        decay = cfg["diagnostic_test_card"]["Y0"] * math.exp(-time / tau) / tau if active else 0.
        factor = cfg["diagnostic_test_card"]["B_mumu"] * decay * c
        sources3.append(factor * distributions.getDistribution[0](p, x, {"mu": 1.}))
        expected3.append(factor * frozen_k(p))
        states3.append(np.broadcast_to(c * p * p * f / (2 * np.pi ** 2 * sr), (3, len(q))))
    sources3, states3, expected3 = map(np.array, (sources3, states3, expected3))
    arrays = {"time_s": times, "x": xs, "p_per_q_MeV": cs, "q": q, "weights_dq": w, "state_normalization_density_MeV3": sref}
    for species, flavor in zip(SPECIES, (0, 0, 1, 1, 2, 2)):
        arrays["source_rhs_" + species + "_dYdt_dq_s_inv"] = sources3[:, flavor]
        arrays["state_dYdq_" + species] = states3[:, flavor]
        arrays["occupation_" + species] = occupation
    np.savez_compressed(out / "diagnostic_symmetric_arrays.npz", **arrays)
    # Native tau occupation may be nonzero; native tau source is exactly zero.
    write_json(out / "array_checks.json", {"array_status": "synthetic fixed-state emitter/map snapshots; not transported or production-consumed source histories",
               "source_node_peak_scaled_error": float(np.max(np.abs(sources3 - expected3)) / np.max(expected3)),
               "zero_tau_source": bool(np.all(sources3[:, 2] == 0)), "cutoff_and_postcutoff_zero": bool(np.all(sources3[time_y >= 18] == 0)),
               "charge_symmetric_sources": True, "charge_symmetric_states": True,
               "state_normalization_q_coefficient": ME ** 3 / (2 * np.pi ** 2 * s0 * cfg["x_initial"] ** 3),
               "source_has_extra_jacobian": "dp/dq=me/x", "entropy_is_comoving_reference": True,
               "renormalization_applied": False})
    uniform = np.linspace(.01, 4., 21)
    nonuniform = .01 + (4. - .01) * np.linspace(0., 1., 21) ** 1.5
    original_weights = independent_simpson(uniform)
    modified_weights = original_weights.copy()
    modified_weights[len(modified_weights) // 2] *= 1.1
    geometry = {"uniform": projection_geometry(uniform), "nonuniform_negative": projection_geometry(nonuniform),
                "custom_weight_negative": {"changed_single_node_factor": 1.1, "change_in_measure_sum_relative": float(np.sum(modified_weights) / np.sum(original_weights) - 1),
                                           "collision_product_measure_changed": True}}
    write_json(out / "collision_geometry_negative_controls.json", geometry)
    write_json(out / "source_grid_results.json", {"rows": rows, "short_window_rows": endpoint_rows, "native_weight_checks": weight_checks,
               "expected_physical_moments": exact_moments().tolist(), "small_positive_q_cutoff_is_not_restored": True,
               "native_collision_execution": False, "native_transport_execution": False})
    after = source_receipt(args.upstream)
    assert before == after
    assert not collision.signatures
    write_json(out / "source_after.json", after)
    write_json(out / "artifact_sha256.json", {path.name: sha(path) for path in sorted(out.iterdir()) if path.is_file()})
    print(json.dumps({"output": str(out), "native_source_rows": len(rows) + len(endpoint_rows), "unchanged_upstream": before == after,
                      "best_full_cap_max_error": min(max(row["max_moment_relative_error"] for row in rows if row["n"] == n and row["case"] == "full_reference_cap_native_weights") for n in cfg["native_n_ladder"]),
                      "production_transport_run": False}, allow_nan=False))


if __name__ == "__main__":
    main()
