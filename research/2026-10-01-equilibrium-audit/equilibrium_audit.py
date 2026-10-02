#!/usr/bin/env python3
"""Six-process static Born consistency diagnostic; not a BBN solver."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
from pathlib import Path
import platform
import sys
from functools import lru_cache

import numpy as np

AUDIT_VERSION = "DMDE-BORN-EQUILIBRIUM-AUDIT-1"
M_E = 0.51099895
DELTA = 1.29333236
TAU_N = 879.4
LABELS = (
    "nue_n_capture", "positron_n_capture", "neutron_beta_decay",
    "nuebar_p_capture", "electron_p_capture", "inverse_neutron_beta_decay",
)
TEMPERATURES = (10., 5., 2., 1., .8, .5, .3, .25, .2, .1, .08, .05, .02)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN_MODULE = ROOT / "provider/code/dmde_v0920_validate_weak_rate_closure.py"


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return value


@lru_cache(maxsize=12)
def unit_rule(order: int) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(order, int) or isinstance(order, bool) or order < 8:
        raise ValueError("quadrature order must be an integer >= 8")
    z, w = np.polynomial.legendre.leggauss(order)
    return (z + 1.) / 2., w / 2.


def fd(energy: np.ndarray, temperature: float) -> np.ndarray:
    temperature = _positive(temperature, "temperature")
    r = np.exp(-np.asarray(energy) / temperature)
    return r / (1. + r)


def analytic_i0() -> float:
    """Exact finite-electron-mass vacuum phase-space integral in MeV^5."""
    q = DELTA / M_E
    return M_E**5 / 60. * (
        math.sqrt(q*q - 1.) * (2*q**4 - 9*q*q - 8.)
        + 15*q*math.acosh(q)
    )


def beta_quadrature(order: int = 96) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return neutrino energy, electron energy, and weighted phase measure."""
    u, w = unit_rule(order)
    electron = M_E + (DELTA - M_E)*u*u
    p = DELTA - electron
    measure = 2*(DELTA - M_E)*u*w
    phase = p*p*electron*np.sqrt((electron - M_E)*(electron + M_E))
    return p, electron, measure*phase


def beta_pair(temperature: float, antineutrino_occupation,
              order: int = 96, tau_n: float = TAU_N) -> dict[str, float]:
    """Integrate beta/inverse beta for arbitrary bounded low-energy occupation."""
    temperature = _positive(temperature, "temperature")
    tau_n = _positive(tau_n, "tau_n")
    p, electron, weight = beta_quadrature(order)
    fe = fd(electron, temperature)
    fbar = np.asarray(antineutrino_occupation(p), dtype=float)
    if fbar.shape != p.shape or not np.all(np.isfinite(fbar)) or np.any((fbar < 0) | (fbar > 1)):
        raise ValueError("antineutrino occupation must have grid shape and lie in [0,1]")
    factor = 1. / (tau_n*analytic_i0())
    return {
        "beta_s_inv": float(factor*np.dot(weight, (1-fe)*(1-fbar))),
        "inverse_s_inv": float(factor*np.dot(weight, fe*fbar)),
        "net_identity_s_inv": float(factor*np.dot(weight, 1-fe-fbar)),
        "inverse_upper_bound_s_inv": float(factor*np.dot(weight, fe)),
    }


def thermal_rates(temperature: float, order: int = 96, tail_in_T: float = 60.,
                  tau_n: float = TAU_N, neutrino_temperature: float | None = None) -> np.ndarray:
    """Three n->p then three p->n rates; zero chemical potentials.

    T_nu may differ from T_gamma to test the domain of detailed balance.
    Capture tails are truncated at tail_in_T times max(T_gamma,T_nu).
    No observational parameter fit, expansion or nuclear evolution is performed.
    """
    tg = _positive(temperature, "temperature")
    tn = tg if neutrino_temperature is None else _positive(neutrino_temperature, "neutrino_temperature")
    tail = _positive(tail_in_T, "tail_in_T")*max(tg, tn)
    factor = 1. / (_positive(tau_n, "tau_n")*analytic_i0())
    u, w = unit_rule(order)
    p = tail*u
    electron = p + DELTA
    phase = p*p*electron*np.sqrt((electron-M_E)*(electron+M_E))
    nue_capture = factor*np.dot(tail*w, phase*fd(p, tn)*(1-fd(electron, tg)))
    electron_capture = factor*np.dot(tail*w, phase*fd(electron, tg)*(1-fd(p, tn)))
    # Squaring u removes the positron threshold's square-root singularity.
    electron = M_E + tail*u*u
    p = electron + DELTA
    phase = p*p*electron*np.sqrt((electron-M_E)*(electron+M_E))
    measure = 2*tail*u*w
    nuebar_capture = factor*np.dot(measure, phase*fd(p, tn)*(1-fd(electron, tg)))
    positron_capture = factor*np.dot(measure, phase*fd(electron, tg)*(1-fd(p, tn)))
    pair = beta_pair(tg, lambda p: fd(p, tn), order, tau_n)
    return np.array([nue_capture, positron_capture, pair["beta_s_inv"],
                     nuebar_capture, electron_capture, pair["inverse_s_inv"]])


def balance_residuals(rates: np.ndarray, temperature: float) -> dict[str, float]:
    """Only meaningful as an equilibrium test for a common-temperature FD state."""
    r = math.exp(-DELTA/temperature)
    n_to_p = float(np.sum(rates[:3]))
    five_p_to_n = float(np.sum(rates[3:5]))
    six_p_to_n = float(np.sum(rates[3:]))
    return {
        "electron_nue_pair_relative_residual": float(rates[4]/rates[0]/r-1),
        "positron_nuebar_pair_relative_residual": float(rates[3]/rates[1]/r-1),
        "beta_inverse_pair_relative_residual": float(rates[5]/rates[2]/r-1),
        "six_process_total_relative_residual": six_p_to_n/n_to_p/r-1,
        "five_process_total_relative_residual": five_p_to_n/n_to_p/r-1,
        "missing_fraction_of_six_p_to_n": float(rates[5]/six_p_to_n),
        "six_over_five_p_to_n_minus_one": six_p_to_n/five_p_to_n-1,
    }


def frozen_comparison(temperature: float, order: int = 96) -> dict[str, float]:
    """Run the preserved v0.9.20 function on a separate composite q quadrature."""
    sys.path.insert(0, str(FROZEN_MODULE.parent))
    try:
        legacy = importlib.import_module(FROZEN_MODULE.stem)
    finally:
        sys.path.pop(0)
    u, w = unit_rule(order)
    tail = 80.*temperature
    # Separate shared-p grid, partitioned at the decay endpoint and capture threshold.
    p = np.concatenate([(DELTA-M_E)*(1-u*u), (DELTA-M_E)+2*M_E*u,
                        (DELTA+M_E)+tail*u*u])
    dp = np.concatenate([2*(DELTA-M_E)*u*w, 2*M_E*w, 2*tail*u*w])
    idx = np.argsort(p)
    p, dp = p[idx], dp[idx]
    f = fd(p, temperature)[None, :]
    result, i0_legacy, _ = legacy.compute_born_process_histories(
        p, dp, np.ones(1), np.array([temperature]), f, f, TAU_N)
    old = np.array([result[label][0] for label in legacy.N_TO_P_LABELS + legacy.P_TO_N_LABELS])
    new = thermal_rates(temperature, order=order, tail_in_T=80.)[:5]
    return {
        "legacy_i0_MeV5": float(i0_legacy),
        "legacy_i0_relative_error": float(i0_legacy/analytic_i0()-1),
        "max_raw_rate_relative_difference": float(np.max(np.abs(old/new-1))),
        "max_relative_difference_after_matching_normalization": float(
            np.max(np.abs(old/new*i0_legacy/analytic_i0()-1))),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report() -> dict:
    rows = []
    for t in TEMPERATURES:
        rates = thermal_rates(t)
        refined = thermal_rates(t, order=192)
        extended = thermal_rates(t, tail_in_T=80.)
        row = {"T_MeV": t, **{label+"_s_inv": float(v) for label, v in zip(LABELS, rates)}}
        row.update(balance_residuals(rates, t))
        row["order_96_to_192_max_relative_change"] = float(np.max(np.abs(rates/refined-1)))
        row["tail_60_to_80_max_relative_change"] = float(np.max(np.abs(rates/extended-1)))
        rows.append(row)
    arbitrary = beta_pair(.1, lambda p: .2+.6*(p/(DELTA-M_E))**2)
    arbitrary["identity_absolute_residual_s_inv"] = abs(
        arbitrary["beta_s_inv"]-arbitrary["inverse_s_inv"]-arbitrary["net_identity_s_inv"])
    # Locate the reference-only threshold for the old 10% total envelope.
    lo, hi = .2, .4
    for _ in range(50):
        mid = (lo+hi)/2
        metrics = balance_residuals(thermal_rates(mid), mid)
        if metrics["six_over_five_p_to_n_minus_one"] > .1:
            lo = mid
        else:
            hi = mid
    checked = [v for row in rows for k, v in row.items()
               if k.endswith("relative_residual") and not k.startswith("five_")]
    convergence = [v for row in rows for k, v in row.items() if k.endswith("max_relative_change")]
    legacy = {str(t): frozen_comparison(t) for t in (5., .8, .3, .2, .1, .05)}
    passed = (max(map(abs, checked)) < 1e-11 and max(convergence) < 1e-10
              and all(v["max_relative_difference_after_matching_normalization"] < 1e-10 for v in legacy.values())
              and arbitrary["identity_absolute_residual_s_inv"] < 1e-16
              and 0 <= arbitrary["inverse_s_inv"] <= arbitrary["inverse_upper_bound_s_inv"]
              and balance_residuals(thermal_rates(.2), .2)["five_process_total_relative_residual"] < -.3)
    return {
        "audit_version": AUDIT_VERSION,
        "status": "PASS_REFERENCE_CONSISTENCY_ONLY" if passed else "FAIL",
        "scope": "Static finite-electron-mass Born rates; no production transport, BBN, observational fit, or discovery claim",
        "constants": {"electron_mass_MeV": M_E, "neutron_proton_mass_difference_MeV": DELTA,
                      "neutron_lifetime_s": TAU_N, "analytic_I0_MeV5": analytic_i0()},
        "assumptions": ["infinitely heavy unpolarized nucleons", "massless neutrinos", "zero chemical potentials",
                        "common-temperature FD equilibrium for balance table", "lifetime-normalized Born matrix element"],
        "provenance": {"python_version": platform.python_version(), "numpy_version": np.__version__,
                       "audit_source_sha256": _sha256(Path(__file__)),
                       "test_source_sha256": _sha256(HERE/"test_equilibrium_audit.py"),
                       "frozen_provider_file": str(FROZEN_MODULE.relative_to(ROOT)),
                       "frozen_provider_source_sha256": _sha256(FROZEN_MODULE)},
        "quadrature": {"order": 96, "refined_order": 192, "capture_tail_in_T": 60., "extended_tail_in_T": 80.,
                       "square_root_endpoints_removed_by_quadratic_substitution": True},
        "equilibrium_table": rows,
        "frozen_provider_comparison": legacy,
        "arbitrary_occupation_example": arbitrary,
        "ten_percent_total_band_crossing_T_MeV": (lo+hi)/2,
        "negative_control": "Omitting inverse beta fails exact equilibrium; large late relative errors do not establish large abundance errors",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE/"outputs")
    args = parser.parse_args()
    report = build_report()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"equilibrium_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    rows = report["equilibrium_table"]
    with (args.output_dir/"equilibrium_rates.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(report["status"])
    print(f"Results: {args.output_dir}")
    return 0 if report["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
