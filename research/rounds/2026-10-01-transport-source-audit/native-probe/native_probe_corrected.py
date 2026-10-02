#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Bounded diagnostic calls into separately installed, unmodified GPL Nudec.

This wrapper does not bundle external source, integrate a trajectory, or certify
production transport. Each grid configuration executes in a fresh subprocess.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
SOURCE = Path("/workspace/shared/dmde-upstream/nudec")
EXPECTED_HEAD = "0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62"
THREAD_ENV = {
    "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1", "NUMBA_NUM_THREADS": "1",
}
DECLARATION = {
    "user_date": "2026-10-01 America/Los_Angeles",
    "x_stop": 4.0, "emission_x_convention": "nextafter(4.0, 0.0), left limit",
    "q_min": 0.01, "emission_refinements": [65, 129, 257, 513, 1025],
    "emission_decay_probabilities": {"mu": 1.0, "pi": 1.0},
    "capture_threshold_convention": "frozen static Born heavy-nucleon limit",
    "threshold_Delta_MeV": 1.29333236, "threshold_reference_me_MeV": 0.51099895,
    "antinue_p_threshold_MeV": 1.80433131, "nue_n_threshold_MeV": 0.0,
    "rhs_x": 4.0, "rhs_n": 21, "rhs_z": 1.4, "rhs_t_seconds": 1.0,
    "rhs_llp_count": 1e-5, "rhs_mass_MeV": 300.0, "rhs_lifetime_seconds": 10.0,
    "rhs_primary_muon_multiplicity": 0.8, "rhs_native_branching_muon": 0.8,
    "rhs_external_charge_pair_B_assumption": 0.4,
    "rhs_other_branchings": [0.0, 0.0, 0.0, 0.0],
    "rhs_fd_convention": "all three flavors f(q)=1/(exp(q/z)+1); native antineutrinos copied",
    "rhs_gates": "on stopPoint=nextafter(x,+inf), off stopPoint=0",
    "worker_timeout_seconds": 180,
    "no_time_integration": True,
}


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(SOURCE), *args], text=True).strip()


def source_snapshot():
    files = git("ls-files", "-z").split("\0")
    files = sorted(name for name in files if name)
    hashes = {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in files}
    snapshot = {
        "source": str(SOURCE), "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "porcelain": git("status", "--porcelain=v1", "--untracked-files=all"),
        "tracked_file_sha256": hashes,
    }
    if snapshot["head"] != EXPECTED_HEAD or snapshot["porcelain"]:
        raise RuntimeError("Native source must match the declared HEAD and be completely clean")
    return snapshot


def package_versions():
    import numpy
    import scipy
    import numba
    import llvmlite
    return {"python": platform.python_version(), "numpy": numpy.__version__,
            "scipy": scipy.__version__, "numba": numba.__version__,
            "llvmlite": llvmlite.__version__}


def exact_moments(lo, hi, muon_mass):
    """Unrenormalized analytic integral of the two native Michel polynomials."""
    lo = max(0.0, min(float(lo), muon_mass / 2.0))
    hi = max(lo, min(float(hi), muon_mass / 2.0))
    zlo, zhi = 2.0 * lo / muon_mass, 2.0 * hi / muon_mass
    def primitive(z):
        return [(4 * z**3 - 3 * z**4), (2 * z**3 - z**4),
                (3 * muon_mass / 10) * (5 * z**4 - 4 * z**5),
                (muon_mass / 20) * (15 * z**4 - 8 * z**5)]
    a, b = primitive(zlo), primitive(zhi)
    higher = {}
    for k in range(2, 6):
        scale = (muon_mass / 2.0) ** k
        electron = lambda zz: scale * (12 * zz ** (k + 3) / (k + 3) - 12 * zz ** (k + 4) / (k + 4))
        muon = lambda zz: scale * (6 * zz ** (k + 3) / (k + 3) - 4 * zz ** (k + 4) / (k + 4))
        higher[str(k)] = [electron(zhi) - electron(zlo), muon(zhi) - muon(zlo), 0.0]
    return {"number": [b[0] - a[0], b[1] - a[1], 0.0],
            "energy_MeV": [b[2] - a[2], b[3] - a[3], 0.0],
            "higher_p_moments_MeV_to_k": higher}


def native_imports():
    sys.path.insert(0, str(SOURCE))
    import Constants
    import Momentum_Grid
    import Distributions
    return Constants, Momentum_Grid, Distributions


def module_metadata():
    modules = {}
    for name, module in sorted(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if file and Path(file).is_relative_to(SOURCE):
            modules[name] = {"path": file, "sha256": hashlib.sha256(Path(file).read_bytes()).hexdigest()}
    return modules


def emission_worker(out, domain, n):
    import numpy as np
    constants, grid, distributions = native_imports()
    x_stop = DECLARATION["x_stop"]
    x = np.nextafter(x_stop, 0.0)
    qmax = x_stop * constants.mmu / 2.0
    if domain == "complete":
        qmax /= constants.me
    grid.setupGrid(qmax, n, DECLARATION["q_min"])
    p = grid.gridVals * constants.me / x
    dp_weights = grid.gridWeights * constants.me / x
    result = distributions.muonDistribution(p, x, DECLARATION["emission_decay_probabilities"])
    number = np.sum(result * dp_weights, axis=1)
    energy = np.sum(result * p * dp_weights, axis=1)
    higher = {str(k): np.sum(result * p**k * dp_weights, axis=1).tolist() for k in range(2, 6)}
    full = exact_moments(0.0, constants.mmu / 2.0, constants.mmu)
    retained = exact_moments(p[0], p[-1], constants.mmu)
    low = exact_moments(0.0, p[0], constants.mmu)
    high = exact_moments(p[-1], constants.mmu / 2.0, constants.mmu)
    thresholds = {}
    for name, threshold in [("nue_n", 0.0), ("antinue_p", DECLARATION["antinue_p_threshold_MeV"])]:
        thresholds[name] = {
            "threshold_MeV": threshold,
            "exact_full_above_threshold": exact_moments(threshold, constants.mmu / 2.0, constants.mmu),
            "exact_retained_above_threshold": exact_moments(max(p[0], threshold), p[-1], constants.mmu),
            "meaning": "Threshold moments only, not cross-section-weighted capture rates",
        }
    with (out / "source_samples.csv").open("x") as handle:
        np.savetxt(handle, np.column_stack((grid.gridVals, p, grid.gridWeights, dp_weights, result.T)),
                   delimiter=",", header="q,p_MeV,native_dq_weight,physical_dp_weight,phi_e,phi_mu,phi_tau", comments="")
    if not np.isfinite(result).all() or not np.isfinite(number).all() or not np.isfinite(energy).all():
        raise FloatingPointError("Non-finite native emission output")
    metadata = {
        "status": "passed", "domain": domain, "n": n, "x": float(x), "x_stop": x_stop,
        "q_min": float(grid.gridVals[0]), "q_max": float(qmax),
        "p_min_MeV": float(p[0]), "p_max_MeV": float(p[-1]),
        "muon_endpoint_MeV": constants.mmu / 2.0,
        "native_me_MeV": constants.me, "native_mmu_MeV": constants.mmu,
        "raw_source_shape": list(result.shape), "preosc_tau_exactly_zero": bool(np.all(result[2] == 0.0)),
        "terminal_native_phi": result[:, -1].tolist(),
        "native_number": number.tolist(), "native_energy_MeV": energy.tolist(),
        "native_higher_p_moments_MeV_to_k": higher,
        "exact_full": full, "exact_retained": retained,
        "exact_missing_below_pmin": low, "exact_missing_above_pmax": high,
        "native_minus_exact_retained_number": (number - retained["number"]).tolist(),
        "native_minus_exact_retained_energy_MeV": (energy - retained["energy_MeV"]).tolist(),
        "thresholds": thresholds, "modules": module_metadata(),
        "normalization": "No sample or moment renormalization; physical dp=(me/x)dq",
        "gate_scope": "Standalone source at x->x_stop from below; native RHS gate is off at x==x_stop",
        "charge_scope": "Native one-spectrum-per-flavor source with nu/antinu symmetry assumed downstream",
    }
    write_json(out / "result.json", metadata)


def rhs_worker(out):
    import numpy as np
    constants, grid, distributions = native_imports()
    x, n = DECLARATION["rhs_x"], DECLARATION["rhs_n"]
    grid.setupGrid(x * constants.mmu / (2.0 * constants.me), n, DECLARATION["q_min"])
    distributions.initDistributions(DECLARATION["rhs_mass_MeV"])
    system = importlib.import_module("System_Nudecoupling")
    collision_module = importlib.import_module("Collision_term.Collision_term_diagonal")
    captured = []
    original_functions = list(distributions.getDistribution)
    def wrap(index, function):
        def capture(ps, xx, decay_probabilities):
            value = function(ps, xx, decay_probabilities)
            captured.append({"index": index, "name": function.__name__, "x": float(xx),
                             "momenta_MeV": ps.copy(), "value": value.copy()})
            return value
        return capture
    distributions.getDistribution = [wrap(i, function) for i, function in enumerate(original_functions)]
    z = DECLARATION["rhs_z"]
    f = 1.0 / (np.exp(grid.gridVals / z) + 1.0)
    state = np.concatenate((f, f, f, [z, DECLARATION["rhs_t_seconds"]]))
    branches = [DECLARATION["rhs_native_branching_muon"], *DECLARATION["rhs_other_branchings"]]
    arguments = (DECLARATION["rhs_lifetime_seconds"], DECLARATION["rhs_mass_MeV"], branches)
    def decay_handler(_):
        return dict(DECLARATION["emission_decay_probabilities"])
    with (out / "fixed_state.csv").open("x") as handle:
        np.savetxt(handle, np.column_stack((np.arange(len(state)), state)), delimiter=",", header="index,state", comments="")
    vectors = {}
    runs = {}
    for tag, count, stop in [
        ("zero_off", 0.0, 0.0), ("zero_on", 0.0, np.nextafter(x, np.inf)),
        ("positive_off", DECLARATION["rhs_llp_count"], 0.0),
        ("positive_on", DECLARATION["rhs_llp_count"], np.nextafter(x, np.inf)),
    ]:
        captured.clear()
        start = time.perf_counter()
        value = system.System_Nudec(x, state.copy(), count, *arguments, stop, decay_handler)
        elapsed = time.perf_counter() - start
        vectors[tag] = value
        with (out / f"rhs_{tag}.csv").open("x") as handle:
            np.savetxt(handle, np.column_stack((np.arange(len(value)), value)), delimiter=",", header="index,dstate_dx", comments="")
        source_metadata = []
        for serial, capture in enumerate(captured):
            array = capture.pop("value")
            momenta = capture.pop("momenta_MeV")
            path = f"preosc_{tag}_{serial}_{capture['name']}.csv"
            with (out / path).open("x") as handle:
                np.savetxt(handle, np.column_stack((grid.gridVals, momenta, array.T)), delimiter=",", header="q,p_MeV,phi_e,phi_mu,phi_tau", comments="")
            source_metadata.append({**capture, "shape": list(array.shape), "file": path,
                                    "finite": bool(np.isfinite(array).all()),
                                    "tau_exactly_zero": bool(np.all(array[2] == 0.0))})
        runs[tag] = {"llp_count": count, "stopPoint": float(stop), "elapsed_seconds": elapsed,
                     "finite_full_vector": bool(np.isfinite(value).all()), "length": len(value),
                     "dzdx": float(value[-2]), "dtdx_seconds": float(value[-1]),
                     "neutrino_max_abs": float(np.max(np.abs(value[:-2]))), "sources": source_metadata}
        if value.shape != (3 * n + 2,) or not np.isfinite(value).all():
            raise FloatingPointError(f"Invalid native RHS vector for {tag}")
    collision = collision_module.Collision_term_diagonal
    delta_gate = vectors["positive_on"] - vectors["positive_off"]
    with (out / "delta_positive_on_minus_off.csv").open("x") as handle:
        np.savetxt(handle, np.column_stack((np.arange(len(delta_gate)), delta_gate)), delimiter=",", header="index,delta_dstate_dx", comments="")
    metadata = {
        "status": "passed", "configuration": DECLARATION, "runs": runs,
        "q_max": float(grid.gridVals[-1]), "native_me_MeV": constants.me,
        "zero_gate_vectors_bitwise_equal": bool(np.array_equal(vectors["zero_on"], vectors["zero_off"])),
        "positive_gate_delta_max_abs_neutrinos": float(np.max(np.abs(delta_gate[:-2]))),
        "positive_gate_delta_dzdx": float(delta_gate[-2]), "positive_gate_delta_dtdx": float(delta_gate[-1]),
        "positive_off_minus_zero_off_dtdx": float(vectors["positive_off"][-1] - vectors["zero_off"][-1]),
        "positive_off_minus_zero_off_dzdx": float(vectors["positive_off"][-2] - vectors["zero_off"][-2]),
        "numba_jit_disabled": bool(importlib.import_module("numba").config.DISABLE_JIT),
        "native_collision_signatures": [str(s) for s in collision.signatures],
        "native_collision_nopython_signatures": [str(s) for s in collision.nopython_signatures],
        "modules": module_metadata(),
        "instrumentation": "getDistribution callables replaced by recording wrappers; each calls original native function and returns its exact unchanged object. No RHS, thermo, collision or mixing mocks/replacements.",
        "gate_scope": "Diagnostic native stopPoint gate changes BOTH source injection and LLP energy-loss term. This is not a frozen-only source-toggle certification.",
        "grid_scope": "Deliberately tiny n=21 fixed complete-support linear grid severely under-resolves FD bulk and is not a converged transport computation.",
        "charge_scope": "Native f_nubar=f_nu.copy() and source factor1/2; no independent charge-asymmetric evolution.",
        "branching_scope": "Native branch0.8 equals primary-muon multiplicity0.8. An external equal-charge-pair assumption labels this pair B=0.4; native SingleShot passes its branch input unchanged and native RHS supplies the nu/antinu factor1/2 itself.",
        "no_time_integration": True, "no_BBN_or_production_witness": True,
    }
    if not collision.nopython_signatures or metadata["numba_jit_disabled"]:
        raise RuntimeError("Expected real native Numba collision compilation")
    if not metadata["zero_gate_vectors_bitwise_equal"]:
        raise AssertionError("Zero-LLP native gate control differs")
    if metadata["positive_gate_delta_max_abs_neutrinos"] <= 0 or metadata["positive_gate_delta_dzdx"] == 0:
        raise AssertionError("Positive-LLP native source/gate did not change coupled RHS")
    if metadata["positive_off_minus_zero_off_dtdx"] == 0:
        raise AssertionError("Positive LLP density did not change Hubble/time RHS")
    write_json(out / "result.json", metadata)


def run(out, rhs_only=False):
    out.mkdir(parents=True, exist_ok=False)
    before = source_snapshot()
    write_json(out / "source_before.json", before)
    write_json(out / "predeclaration.json", DECLARATION)
    write_json(out / "runtime.json", {"versions": package_versions(), "python_executable": sys.executable,
                                     "thread_environment": {k: os.environ.get(k) for k in THREAD_ENV},
                                     "wrapper_path": str(Path(__file__).resolve()),
                                     "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    jobs = [(f"emission_{domain}_n{n}", ["emission", "--domain", domain, "--n", str(n)])
            for domain in ("clipped", "complete") for n in DECLARATION["emission_refinements"]]
    jobs.append(("rhs_n21", ["rhs"]))
    if rhs_only:
        jobs = jobs[-1:]
    outcomes = []
    try:
        for name, args in jobs:
            child = out / name
            child.mkdir()
            command = [sys.executable, "-B", str(Path(__file__).resolve()), *args, "--out", str(child)]
            started = time.perf_counter()
            try:
                result = subprocess.run(command, cwd=SOURCE, env={**os.environ, **THREAD_ENV},
                                        capture_output=True, text=True, timeout=DECLARATION["worker_timeout_seconds"])
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
                outcome = {"name": name, "returncode": code, "timeout": False}
            except subprocess.TimeoutExpired as error:
                stdout, stderr = error.stdout or "", error.stderr or ""
                if isinstance(stdout, bytes): stdout = stdout.decode(errors="replace")
                if isinstance(stderr, bytes): stderr = stderr.decode(errors="replace")
                outcome = {"name": name, "returncode": None, "timeout": True}
            (child / "stdout.log").write_text(stdout)
            (child / "stderr.log").write_text(stderr)
            outcome.update({"elapsed_seconds": time.perf_counter() - started, "command": command})
            outcomes.append(outcome)
            print(json.dumps(outcome), flush=True)
    finally:
        after = source_snapshot()
        write_json(out / "source_after.json", after)
        unchanged = before == after
        write_json(out / "execution.json", {"jobs": outcomes, "source_unchanged": unchanged,
                                            "all_jobs_completed_successfully": len(outcomes) == len(jobs) and all(o["returncode"] == 0 for o in outcomes)})
        if not unchanged:
            raise AssertionError("Native source provenance changed during diagnostics")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "run-rhs", "emission", "rhs"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--domain", choices=["clipped", "complete"])
    parser.add_argument("--n", type=int)
    args = parser.parse_args()
    if args.mode in ("run", "run-rhs"):
        run(args.out, rhs_only=args.mode == "run-rhs")
    else:
        try:
            if args.mode == "emission": emission_worker(args.out, args.domain, args.n)
            else: rhs_worker(args.out)
        except Exception:
            failure = {"status": "failed", "traceback": traceback.format_exc()}
            write_json(args.out / "failure.json", failure)
            raise


if __name__ == "__main__":
    main()
