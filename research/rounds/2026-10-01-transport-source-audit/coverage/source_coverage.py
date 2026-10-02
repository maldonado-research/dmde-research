"""Independent continuous Michel endpoint-coverage diagnostic; no evolution.

Integrates the public prescribed source shapes without importing a producer,
validator, Nudec, or PRIMAT module. The optional source directories are used
only to record hashes/commits. Default execution prints JSON and changes no
files; --output creates a new receipt and refuses overwrite.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad, simpson

FROZEN_MUON_MASS = 105.6583755
FROZEN_ELECTRON_MASS = 0.51099895
DELTA_NP = 1.29333236
NUDEC_MUON_MASS = 105.7
NUDEC_ELECTRON_MASS = 0.5109989
X_STOP_REFERENCE = 16.993868549367075


def density(z, flavour):
    if flavour == "electron":
        return 12.0 * z**2 * (1.0 - z)
    if flavour == "muon":
        return 2.0 * z**2 * (3.0 - 2.0 * z)
    raise ValueError(flavour)


def full_dimensionless_moment(flavour, k):
    if flavour == "electron":
        return 12.0 / ((k + 3) * (k + 4))
    return 2.0 * (k + 6) / ((k + 3) * (k + 4))


def retained_fraction(flavour, k, c):
    c = min(1.0, max(0.0, c))
    if flavour == "electron":
        return (k + 4) * c**(k + 3) - (k + 3) * c**(k + 4)
    return (3 * (k + 4) * c**(k + 3) - 2 * (k + 3) * c**(k + 4)) / (k + 6)


def source_case(cutoff, muon_mass):
    endpoint = muon_mass / 2
    c = min(1.0, max(0.0, cutoff / endpoint))
    result = {"physical_cutoff_MeV": cutoff, "source_endpoint_MeV": endpoint,
              "retained_endpoint_fraction": c, "flavours": {}}
    for flavour in ("electron", "muon"):
        rows = []
        for k in range(6):
            full = endpoint**k * full_dimensionless_moment(flavour, k)
            fraction = retained_fraction(flavour, k, c)
            rows.append({"k": k, "full_moment_MeV_power_k": full,
                         "retained_moment_MeV_power_k": full * fraction,
                         "retained_fraction": fraction,
                         "omitted_upper_tail_fraction": 1.0 - fraction})
        number = rows[0]["retained_moment_MeV_power_k"]
        mean = rows[1]["retained_moment_MeV_power_k"] / number if number else None
        full_mean = rows[1]["full_moment_MeV_power_k"]
        result["flavours"][flavour] = {
            "moments": rows, "conditional_mean_energy_MeV": mean,
            "full_mean_energy_MeV": full_mean,
            "conditional_mean_over_full_mean": mean / full_mean if mean is not None else None,
        }
    return result


def capture_kernel(energy, kind, me=FROZEN_ELECTRON_MASS, delta=DELTA_NP):
    electron_energy = energy + delta if kind == "nu_n" else energy - delta
    if electron_energy < me:
        return 0.0
    return electron_energy * math.sqrt(max(electron_energy**2 - me**2, 0.0))


def capture_integral(cutoff, kind, muon_mass=FROZEN_MUON_MASS,
                     me=FROZEN_ELECTRON_MASS, delta=DELTA_NP):
    endpoint = muon_mass / 2
    lo = max(0.0, me - delta) if kind == "nu_n" else me + delta
    hi = min(endpoint, max(0.0, cutoff))
    if hi <= lo:
        return 0.0
    # Adaptive integration in physical neutrino energy; threshold is a bound.
    return quad(lambda energy: density(energy / endpoint, "electron") / endpoint
                * capture_kernel(energy, kind, me, delta), lo, hi,
                epsabs=1e-11, epsrel=2e-12, limit=200)[0]


def capture_gl(cutoff, kind, n):
    """Independent threshold-smoothed Gauss rule: E=E_threshold+u^2."""
    endpoint = FROZEN_MUON_MASS / 2
    lo = 0.0 if kind == "nu_n" else DELTA_NP + FROZEN_ELECTRON_MASS
    hi = min(endpoint, cutoff)
    if hi <= lo:
        return 0.0
    nodes, weights = np.polynomial.legendre.leggauss(n)
    umax = math.sqrt(hi - lo)
    u = umax * (nodes + 1) / 2
    energies = lo + u**2
    kernel = np.array([capture_kernel(float(e), kind) for e in energies])
    integrand = density(energies / endpoint, "electron") / endpoint * kernel * 2 * u
    return float(np.dot(weights, integrand) * umax / 2)


def capture_case(cutoffs):
    endpoint = FROZEN_MUON_MASS / 2
    result = {}
    for kind, cutoff in cutoffs.items():
        full = capture_integral(endpoint, kind)
        partial = capture_integral(cutoff, kind)
        result[kind] = {"neutrino_energy_ceiling_MeV": cutoff,
                        "full_proxy_MeV2": full,
                        "retained_proxy_MeV2": partial,
                        "retained_proxy_fraction": partial / full,
                        "omitted_proxy_fraction": 1 - partial / full}
    return result


def controls():
    endpoint = FROZEN_MUON_MASS / 2
    c_native = NUDEC_ELECTRON_MASS
    moment_errors = []
    for flavour in ("electron", "muon"):
        for k in range(6):
            full = full_dimensionless_moment(flavour, k)
            for c in (0.0, 0.05, c_native, 0.9, 1.0):
                numeric = quad(lambda z: z**k * density(z, flavour), 0, c,
                               epsabs=1e-14, epsrel=2e-12)[0]
                analytic = full * retained_fraction(flavour, k, c)
                moment_errors.append(abs(numeric - analytic) / full)
    assert max(moment_errors) < 2e-13
    endpoint_controls = all(retained_fraction(f, k, 0) == 0
                            and retained_fraction(f, k, 1) == 1
                            and retained_fraction(f, k, -1) == 0
                            and retained_fraction(f, k, 2) == 1
                            for f in ("electron", "muon") for k in range(6))
    assert endpoint_controls
    monotone = all(np.all(np.diff([retained_fraction(f, k, c)
                                  for c in np.linspace(0, 1, 101)]) >= -1e-14)
                   for f in ("electron", "muon") for k in range(6))
    assert monotone
    massless_errors = []
    for kind in ("nu_n", "antinu_p"):
        full = capture_integral(endpoint, kind, me=0.0, delta=0.0)
        partial = capture_integral(c_native * endpoint, kind, me=0.0, delta=0.0)
        massless_errors.append(abs(partial / full - retained_fraction("electron", 2, c_native)))
    assert max(massless_errors) < 2e-13
    threshold = DELTA_NP + FROZEN_ELECTRON_MASS
    threshold_values = [capture_integral(c, "antinu_p") for c in (0.0, threshold / 2, threshold)]
    assert all(value == 0 for value in threshold_values)
    gl_errors = []
    for kind in ("nu_n", "antinu_p"):
        for cutoff in (7 * FROZEN_ELECTRON_MASS, c_native * endpoint, endpoint):
            reference = capture_integral(cutoff, kind)
            for n in (64, 128):
                gl_errors.append(abs(capture_gl(cutoff, kind, n) / reference - 1))
    assert max(gl_errors) < 1e-10
    # Fixed-domain refinement converges to clipped moments, not full moments.
    refinement = []
    for n in (21, 41, 81, 161):
        z = np.linspace(0.0, c_native, n)
        for flavour in ("electron", "muon"):
            numeric = float(simpson(density(z, flavour), x=z))
            exact_clipped = retained_fraction(flavour, 0, c_native)
            refinement.append({"n_points": n, "flavour": flavour,
                               "number_moment": numeric,
                               "error_relative_to_clipped_target": numeric / exact_clipped - 1,
                               "error_relative_to_full_target": numeric - 1})
    assert max(abs(row["error_relative_to_clipped_target"]) for row in refinement) < 1e-12
    assert min(abs(row["error_relative_to_full_target"]) for row in refinement) > 0.65
    # Deliberate renormalization can make number look complete while losing energy.
    normalization = source_case(c_native * endpoint, FROZEN_MUON_MASS)
    normalization_control = {}
    for flavour, values in normalization["flavours"].items():
        ratio = values["conditional_mean_over_full_mean"]
        normalization_control[flavour] = {"renormalized_number_moment": 1.0,
                                           "renormalized_energy_over_full_energy": ratio}
        assert ratio < 0.7
    # The formerly squared-only antineutrino condition admits a negative branch.
    old_branch = quad(lambda energy: density(energy / endpoint, "electron") / endpoint
                      * (energy - DELTA_NP)
                      * math.sqrt(max((energy - DELTA_NP)**2 - FROZEN_ELECTRON_MASS**2, 0.0)),
                      0, DELTA_NP - FROZEN_ELECTRON_MASS,
                      epsabs=1e-16, epsrel=2e-12)[0]
    assert old_branch < 0
    return {"analytic_moments_vs_adaptive_quadrature_max_abs_error_relative_full": max(moment_errors),
            "zero_full_and_clamped_endpoint_controls_passed": endpoint_controls,
            "monotonicity_control_passed": monotone,
            "massless_zero_delta_proxy_vs_second_moment_max_abs_fraction_error": max(massless_errors),
            "antinu_proxy_below_and_at_threshold_values_MeV2": threshold_values,
            "threshold_smoothed_GL64_GL128_vs_adaptive_max_abs_relerr": max(gl_errors),
            "fixed_clipped_domain_refinement_negative_control": refinement,
            "renormalized_clipped_source_negative_control": normalization_control,
            "unphysical_squared_only_antinu_branch_negative_control_MeV2": old_branch,
            "all_assertions_passed": True}


def source_provenance(directory, paths):
    if directory is None:
        return None
    directory = directory.resolve()
    commit = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"],
                            text=True, check=True, capture_output=True).stdout.strip()
    return {"commit": commit, "files_sha256": {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    optimize_env = os.environ.get("PYTHONOPTIMIZE", "")
    try:
        env_optimization_requested = int(optimize_env or "0") != 0
    except ValueError:
        env_optimization_requested = bool(optimize_env)
    if sys.flags.optimize or env_optimization_requested:
        parser.error("Scientific controls require assertions enabled; refusing optimized Python or nonzero PYTHONOPTIMIZE")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--nudec-dir", type=Path)
    parser.add_argument("--primat-dir", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f"Refusing to overwrite existing output: {args.output}")
    endpoint = FROZEN_MUON_MASS / 2
    native_endpoint = NUDEC_MUON_MASS / 2
    native_cutoff = NUDEC_ELECTRON_MASS * native_endpoint
    qmax_native = X_STOP_REFERENCE * native_endpoint
    p_e_max = 7 * FROZEN_ELECTRON_MASS
    e_e_max = math.hypot(p_e_max, FROZEN_ELECTRON_MASS)
    weak_ceilings = {"nu_n": e_e_max - DELTA_NP, "antinu_p": e_e_max + DELTA_NP}
    output = {
        "scope": "continuous prescribed-source moment and zero-blocking static Born capture-proxy coverage only; no evolved occupations, transport solution, weak-rate solution, time-integrated yield, BBN or abundance prediction",
        "source_contract": "massless charged-lepton Michel source shapes; w_e=12z^2(1-z), w_mu=2z^2(3-2z), 0<=z<=1; dN/dE=w(E/L)/L, L=m_mu/2; no renormalization after clipping",
        "capture_proxy_contract": "electron-flavour source averaged against (E+Delta)*sqrt((E+Delta)^2-me^2) for nu_n; physical E>=Delta+me antinu_p branch with (E-Delta)*sqrt((E-Delta)^2-me^2); no blocking, recoil, radiative, finite-nucleon-mass or plasma corrections; not occupied-state rates",
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "constants_MeV": {"frozen_muon_mass": FROZEN_MUON_MASS,
                           "frozen_electron_mass": FROZEN_ELECTRON_MASS,
                           "delta_np": DELTA_NP,
                           "nudec_muon_mass": NUDEC_MUON_MASS,
                           "nudec_electron_mass": NUDEC_ELECTRON_MASS},
        "reference_x_stop": X_STOP_REFERENCE,
        "source_domain_arithmetic": {"native_qmax_reference": qmax_native,
            "native_final_injection_limit_pmax_MeV": native_cutoff,
            "native_endpoint_complete_qmax_reference": qmax_native / NUDEC_ELECTRON_MASS,
            "frozen_endpoint_complete_qmax_with_frozen_me_reference": X_STOP_REFERENCE * endpoint / FROZEN_ELECTRON_MASS,
            "native_clipping_onset_x_over_xstop": NUDEC_ELECTRON_MASS,
            "frozen_clipping_onset_x_over_xstop_at_native_domain": native_cutoff / endpoint,
            "time_dependence": "for fixed qmax, pmax(x)=qmax*me/x; x_stop snapshot is the x->x_stop^- limit because native injection uses x<x_stop; no t(x) integration is done"},
        "source_cases": {
            "native_source_at_native_final_injection_domain": source_case(native_cutoff, NUDEC_MUON_MASS),
            "frozen_source_at_unmodified_native_final_injection_domain": source_case(native_cutoff, FROZEN_MUON_MASS),
            "frozen_source_at_mass_aligned_but_uncorrected_domain": source_case(NUDEC_ELECTRON_MASS * endpoint, FROZEN_MUON_MASS),
            "frozen_source_endpoint_complete_control": source_case(endpoint, FROZEN_MUON_MASS),
        },
        "local_domain_snapshots_native_source": [
            {"x_over_xstop": scale, "retained_fractions": {
                flavour: {"number": retained_fraction(flavour, 0, NUDEC_ELECTRON_MASS / scale),
                          "energy": retained_fraction(flavour, 1, NUDEC_ELECTRON_MASS / scale)}
                for flavour in ("electron", "muon")}}
            for scale in (0.25, 0.5, NUDEC_ELECTRON_MASS, 0.75, 1.0)],
        "frozen_capture_proxy_at_native_final_injection_domain": capture_case({"nu_n": native_cutoff, "antinu_p": native_cutoff}),
        "weak_quadrature_domain_diagnostic": {
            "T_gamma_MeV": 0.1, "electron_p_over_me_ceiling": 7.0,
            "electron_momentum_ceiling_MeV": p_e_max,
            "electron_energy_ceiling_MeV": e_e_max,
            "mapping": "PRIMAT thermal weak quadrature uses dimensionless electron momentum pmax=max(7,30T_gamma/me); static nu_n E_nu=E_e-Delta, antinu_p E_antinu=E_e+Delta; these are integration-domain ceilings, not the last interior Gauss node",
            "channel_specific_frozen_source_proxy_coverage": capture_case(weak_ceilings),
            "channel_specific_frozen_source_number_energy_coverage": {
                kind: source_case(cutoff, FROZEN_MUON_MASS) for kind, cutoff in weak_ceilings.items()},
            "interpretation": "coverage of a hypothetical full frozen source under these ceilings; no nonthermal PRIMAT adapter or rate evolution is executed"},
        "controls": controls(),
        "provenance": {
            "nudec": source_provenance(args.nudec_dir, ["Core.py", "System_Nudecoupling.py", "Distributions.py", "Constants.py", "Momentum_Grid.py"]),
            "primat": source_provenance(args.primat_dir, ["primat/weak_rates/corrections.py", "primat/constants.py"]),
            "executed_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "upstream_modules_imported_or_executed": False},
    }
    rendered = json.dumps(output, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
