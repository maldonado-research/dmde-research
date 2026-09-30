#!/usr/bin/env python3
"""Machine-derive the DMDE v0.9.20 coarse/fine convergence decision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from dmde_v0920_meaningful_refinement import evaluate_meaningful_refinement

Y_P_MAX = 1e-4
DH_REL_MAX = 5e-3
NEFF_MAX = 1e-3
RATE_INTEGRAL_REL_MAX = 5e-3
H_INTEGRAL_REL_MAX = 1e-3
RATE_HISTORY_L1_REL_MAX = 5e-3
H_HISTORY_L1_REL_MAX = 1e-3
RATE_HISTORY_MAX_GLOBAL_REL_MAX = 2e-2
H_HISTORY_MAX_GLOBAL_REL_MAX = 5e-3
SPECTRAL_MOMENT_L1_REL_MAX = 5e-3
SPECTRAL_MOMENT_MAX_GLOBAL_REL_MAX = 2e-2

FROZEN_EQUAL_SCALARS = (
    "schema_version", "blind_id", "source_payload_sha256",
    "source_card_version", "source_payload_schema", "source_package_version",
    "source_card_json_sha256", "source_payload_manifest_sha256",
    "source_payload_schema_document_sha256", "source_tau_s", "source_m_mu_MeV",
    "source_mass_MeV", "source_Y0", "source_epsilon", "source_B_mumu",
    "source_B_ee_plus_EMlike_neutral_effective", "source_native_muon_multiplicity",
    "source_native_pion_multiplicity", "source_f_EM_integrated",
    "source_f_nu_integrated", "source_lifetime_factor", "neutron_lifetime_s",
)


def _scalar(data, key):
    value = np.asarray(data[key])
    if value.size != 1:
        raise ValueError(f"{key} is not scalar")
    return value.reshape(-1)[0].item()


def _integral(data, key):
    t = np.asarray(data["t_s"], dtype=float)
    values = np.asarray(data[key], dtype=float)
    return float(np.trapezoid(values, t))


def _history_difference(coarse, fine, key):
    coarse_t = np.asarray(coarse["t_s"], dtype=float)
    fine_t = np.asarray(fine["t_s"], dtype=float)
    coarse_values = np.asarray(coarse[key], dtype=float)
    fine_values = np.asarray(fine[key], dtype=float)
    return _series_difference(coarse_t, coarse_values, fine_t, fine_values)


def _spectral_moment(data, key, power):
    q = np.asarray(data["q_grid"], dtype=float)
    qw = np.asarray(data["q_weights"], dtype=float)
    pscale = np.asarray(data["p_per_q_MeV"], dtype=float)
    distribution = np.asarray(data[key], dtype=float)
    return np.sum(distribution * qw[None, :] * q[None, :] ** power * pscale[:, None] ** (power + 1), axis=1)


def _series_difference(coarse_t, coarse_values, fine_t, fine_values):
    start = max(float(coarse_t[0]), float(fine_t[0]))
    stop = min(float(coarse_t[-1]), float(fine_t[-1]))
    union = np.unique(np.concatenate((coarse_t[(coarse_t >= start) & (coarse_t <= stop)], fine_t[(fine_t >= start) & (fine_t <= stop)])))
    coarse_on_union = np.interp(union, coarse_t, coarse_values)
    fine_on_union = np.interp(union, fine_t, fine_values)
    difference = np.abs(coarse_on_union - fine_on_union)
    denominator = max(float(np.trapezoid(np.abs(fine_on_union), union)), 1e-300)
    l1 = float(np.trapezoid(difference, union)) / denominator
    max_global = float(np.max(difference)) / max(float(np.max(np.abs(fine_on_union))), 1e-300)
    return l1, max_global


def _compare_refinement_impl(coarse_npz, fine_npz, coarse_metrics=None, fine_metrics=None):
    errors = []
    metrics = {}
    try:
        coarse = np.load(coarse_npz, allow_pickle=False)
        fine = np.load(fine_npz, allow_pickle=False)
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"bridge load failure: {exc}"], "metrics": {}}
    for key in FROZEN_EQUAL_SCALARS:
        if key not in coarse.files or key not in fine.files:
            errors.append(f"coarse/fine missing frozen scalar {key}")
        elif str(_scalar(coarse, key)) != str(_scalar(fine, key)):
            errors.append(f"coarse/fine {key} mismatch")
    coarse_nq = len(coarse["q_grid"])
    fine_nq = len(fine["q_grid"])
    coarse_nt = len(coarse["t_s"])
    fine_nt = len(fine["t_s"])
    metrics.update({
        "coarse_momentum_bins": coarse_nq,
        "fine_momentum_bins": fine_nq,
        "coarse_time_points": coarse_nt,
        "fine_time_points": fine_nt,
    })
    if fine_nq <= coarse_nq:
        errors.append("fine momentum grid is not a strict bin-count refinement")
    if fine_nt <= coarse_nt:
        errors.append("fine time grid is not a strict point-count refinement")
    coarse_t_end = float(np.asarray(coarse["t_s"], float)[-1])
    fine_t_end = float(np.asarray(fine["t_s"], float)[-1])
    if fine_t_end + 1e-9 < coarse_t_end:
        errors.append("fine history ends earlier than coarse history")

    # Bin counts alone are not evidence of physical refinement: an irrelevant
    # tail node can increase Nq or Nt without resolving the source, freeze-out,
    # or antineutrino threshold.  Require at least a 10% reduction in all four
    # problem-relevant maximum cell widths.
    meaningful = evaluate_meaningful_refinement(
        {
            "t_s": np.asarray(coarse["t_s"], dtype=float),
            "T_gamma_MeV": np.asarray(coarse["T_gamma_MeV"], dtype=float),
            "q_grid": np.asarray(coarse["q_grid"], dtype=float),
            "p_per_q_MeV": np.asarray(coarse["p_per_q_MeV"], dtype=float),
            "tau_s": float(_scalar(coarse, "source_tau_s")),
        },
        {
            "t_s": np.asarray(fine["t_s"], dtype=float),
            "T_gamma_MeV": np.asarray(fine["T_gamma_MeV"], dtype=float),
            "q_grid": np.asarray(fine["q_grid"], dtype=float),
            "p_per_q_MeV": np.asarray(fine["p_per_q_MeV"], dtype=float),
            "tau_s": float(_scalar(fine, "source_tau_s")),
        },
    )
    metrics["meaningful_refinement"] = meaningful
    for key, value in meaningful.get("ratios", {}).items():
        metrics[f"meaningful_{key}"] = value
    if meaningful.get("status") != "PASS":
        errors.extend(
            f"meaningful refinement failed: {name}"
            for name in meaningful.get("failed_checks", ["unknown"])
        )

    yp_c = float(_scalar(coarse, "Yp_model"))
    yp_f = float(_scalar(fine, "Yp_model"))
    dh_c = float(_scalar(coarse, "DH_x1e5_model"))
    dh_f = float(_scalar(fine, "DH_x1e5_model"))
    ne_c = float(_scalar(coarse, "Neff_CMB_model"))
    ne_f = float(_scalar(fine, "Neff_CMB_model"))
    delta_yp = abs(yp_f - yp_c)
    delta_dh = abs(dh_f - dh_c) / abs(dh_f) if dh_f else float("inf")
    delta_neff = abs(ne_f - ne_c)
    metrics.update({
        "convergence_delta_Yp_abs": delta_yp,
        "convergence_delta_DH_rel": delta_dh,
        "convergence_delta_Neff_abs": delta_neff,
        "Yp_coarse": yp_c, "Yp_fine": yp_f,
        "DH_x1e5_coarse": dh_c, "DH_x1e5_fine": dh_f,
        "Neff_coarse": ne_c, "Neff_fine": ne_f,
    })
    if delta_yp > Y_P_MAX:
        errors.append("Yp refinement ceiling failed")
    if delta_dh > DH_REL_MAX:
        errors.append("D/H refinement ceiling failed")
    if delta_neff > NEFF_MAX:
        errors.append("Neff refinement ceiling failed")

    for key, label, threshold in (
        ("lambda_n_to_p_s_inv", "lambda_np", RATE_INTEGRAL_REL_MAX),
        ("lambda_p_to_n_s_inv", "lambda_pn", RATE_INTEGRAL_REL_MAX),
        ("H_s_inv", "H", H_INTEGRAL_REL_MAX),
    ):
        coarse_integral = _integral(coarse, key)
        fine_integral = _integral(fine, key)
        rel = abs(fine_integral - coarse_integral) / max(abs(fine_integral), 1e-300)
        metrics[f"convergence_{label}_integral_rel"] = rel
        metrics[f"coarse_{label}_integral"] = coarse_integral
        metrics[f"fine_{label}_integral"] = fine_integral
        if rel > threshold:
            errors.append(f"{label} integrated-history refinement ceiling failed")

    for key, label, l1_ceiling, max_ceiling in (
        ("lambda_n_to_p_s_inv", "lambda_np", RATE_HISTORY_L1_REL_MAX, RATE_HISTORY_MAX_GLOBAL_REL_MAX),
        ("lambda_p_to_n_s_inv", "lambda_pn", RATE_HISTORY_L1_REL_MAX, RATE_HISTORY_MAX_GLOBAL_REL_MAX),
        ("H_s_inv", "H", H_HISTORY_L1_REL_MAX, H_HISTORY_MAX_GLOBAL_REL_MAX),
    ):
        l1, max_global = _history_difference(coarse, fine, key)
        metrics[f"convergence_{label}_history_L1_rel"] = l1
        metrics[f"convergence_{label}_history_max_global_rel"] = max_global
        if l1 > l1_ceiling:
            errors.append(f"{label} local-history L1 refinement ceiling failed")
        if max_global > max_ceiling:
            errors.append(f"{label} local-history maximum refinement ceiling failed")

    for key, label in (
        ("T_gamma_MeV", "T_gamma"),
        ("p_per_q_MeV", "p_per_q"),
    ):
        l1, max_global = _history_difference(coarse, fine, key)
        metrics[f"convergence_{label}_history_L1_rel"] = l1
        metrics[f"convergence_{label}_history_max_global_rel"] = max_global
        if l1 > H_HISTORY_L1_REL_MAX or max_global > H_HISTORY_MAX_GLOBAL_REL_MAX:
            errors.append(f"{label} local-history refinement ceiling failed")
    coarse_scale = np.asarray(coarse["scale_factor"], dtype=float)
    fine_scale = np.asarray(fine["scale_factor"], dtype=float)
    scale_l1, scale_max = _series_difference(
        np.asarray(coarse["t_s"], dtype=float), coarse_scale / coarse_scale[0],
        np.asarray(fine["t_s"], dtype=float), fine_scale / fine_scale[0],
    )
    metrics["convergence_scale_factor_history_L1_rel"] = scale_l1
    metrics["convergence_scale_factor_history_max_global_rel"] = scale_max
    if scale_l1 > H_HISTORY_L1_REL_MAX or scale_max > H_HISTORY_MAX_GLOBAL_REL_MAX:
        errors.append("scale_factor local-history refinement ceiling failed")

    coarse_t = np.asarray(coarse["t_s"], dtype=float)
    fine_t = np.asarray(fine["t_s"], dtype=float)
    for flavor in ("f_nue", "f_nuebar", "f_numu", "f_numubar", "f_nutau", "f_nutaubar"):
        for power in (2, 3):
            coarse_moment = _spectral_moment(coarse, flavor, power)
            fine_moment = _spectral_moment(fine, flavor, power)
            l1, max_global = _series_difference(coarse_t, coarse_moment, fine_t, fine_moment)
            stem = f"convergence_{flavor}_p{power}_moment"
            metrics[f"{stem}_L1_rel"] = l1
            metrics[f"{stem}_max_global_rel"] = max_global
            if l1 > SPECTRAL_MOMENT_L1_REL_MAX:
                errors.append(f"{flavor} p^{power} spectral-moment L1 refinement ceiling failed")
            if max_global > SPECTRAL_MOMENT_MAX_GLOBAL_REL_MAX:
                errors.append(f"{flavor} p^{power} spectral-moment maximum refinement ceiling failed")

    if coarse_metrics is not None and coarse_metrics.get("run_role") != "coarse":
        errors.append("coarse bridge metadata run_role mismatch")
    if fine_metrics is not None and fine_metrics.get("run_role") != "fine":
        errors.append("fine bridge metadata run_role mismatch")
    if coarse_metrics is not None and fine_metrics is not None:
        coarse_margin = float(coarse_metrics.get("endpoint_relative_margin", -1))
        fine_margin = float(fine_metrics.get("endpoint_relative_margin", -1))
        metrics["coarse_endpoint_relative_margin"] = coarse_margin
        metrics["fine_endpoint_relative_margin"] = fine_margin
        if fine_margin + 1e-12 < coarse_margin:
            errors.append("fine momentum domain is narrower than coarse domain")

    coarse.close()
    fine.close()
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "metrics": metrics}


def compare_refinement(coarse_npz, fine_npz, coarse_metrics=None, fine_metrics=None):
    try:
        return _compare_refinement_impl(coarse_npz, fine_npz, coarse_metrics, fine_metrics)
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"refinement comparison failure: {exc}"], "metrics": {}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("coarse_bridge_npz")
    parser.add_argument("fine_bridge_npz")
    parser.add_argument("--out-json", default="DMDE_v0920_refinement_validation.json")
    args = parser.parse_args()
    result = compare_refinement(args.coarse_bridge_npz, args.fine_bridge_npz)
    Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"REFINEMENT VALIDATION {result['status']}")
    if result["status"] != "PASS":
        for error in result["errors"]:
            print("ERROR:", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
