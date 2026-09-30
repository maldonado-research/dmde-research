#!/usr/bin/env python3
"""Audit the frozen DMDE pair geometry and emit deterministic design receipts.

This program uses only the frozen v0.9.19 source cards and payloads.  It does
not evolve neutrinos, calculate weak rates, or predict primordial abundances.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA = "DMDE-FROZEN-PAIR-DIFFERENTIAL-DESIGN-v0.9.20"
EXPECTED_IDS = ("DMDE-SPEC-V099-4Q7N", "DMDE-SPEC-V099-8M2K")
PAYLOAD_NAMES = {
    "DMDE-SPEC-V099-4Q7N": "DMDE-SPEC-V099-4Q7N_spectral_payload_v099.npz",
    "DMDE-SPEC-V099-8M2K": "DMDE-SPEC-V099-8M2K_spectral_payload_v099.npz",
}
EXPECTED_PAYLOAD_SHA256 = {
    "DMDE-SPEC-V099-4Q7N": "f5f9ad03206572f12103655714cf5c814287ba07dd45bdc3c6185312a3553dcb",
    "DMDE-SPEC-V099-8M2K": "ad86c5d4161afd12dde76e83bb19c9b313197fc31703baaf00cad7ba9f478c3e",
}
ELASTICITY_ERROR_TARGETS = (0.1, 0.05, 0.02, 0.01, 0.005, 0.001)
ELASTICITY_MAGNITUDES = (1.0, 0.3, 0.1, 0.03, 0.01)


class AuditError(RuntimeError):
    """Raised when the frozen inputs fail an identity required by the result."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def source_amplitudes(card: dict[str, Any]) -> dict[str, float]:
    """Return the two independent separable source amplitudes.

    `nu_number_per_species` multiplies each one of Fe, Fe, Fmu, Fmu.
    `em_energy_MeV` multiplies the common exp(-t/tau)/tau time law.
    The finite t<18 tau completeness is kept separate because it cancels from
    all pair ratios.
    """
    return {
        "nu_number_per_species": float(card["B_mumu"]) * float(card["Y0"]),
        "em_energy_MeV": (
            float(card["f_EM_integrated"])
            * float(card["mass_MeV"])
            * float(card["Y0"])
        ),
        "nu_energy_MeV": (
            float(card["f_nu_integrated"])
            * float(card["mass_MeV"])
            * float(card["Y0"])
        ),
        "parent_rest_energy_MeV": float(card["mass_MeV"]) * float(card["Y0"]),
    }


def inspect_payloads(provider_root: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    payload_dir = provider_root / "payloads"
    arrays: dict[str, dict[str, np.ndarray]] = {}
    hashes: dict[str, str] = {}
    for card in cards:
        blind_id = str(card["blind_id"])
        path = payload_dir / PAYLOAD_NAMES[blind_id]
        require(path.is_file(), f"missing payload: {path}")
        digest = sha256_file(path)
        require(digest == EXPECTED_PAYLOAD_SHA256[blind_id], f"payload hash mismatch: {blind_id}")
        hashes[blind_id] = digest
        with np.load(path, allow_pickle=False) as data:
            arrays[blind_id] = {name: np.array(data[name], copy=True) for name in data.files}

    low, high = (arrays[blind_id] for blind_id in EXPECTED_IDS)
    for name in ("t_s", "y_t_over_tau", "x", "E_MeV", "Fe", "Fmu", "Q_pi_charged_over_s"):
        require(np.array_equal(low[name], high[name]), f"pair common-mode array mismatch: {name}")

    ratio_metrics: dict[str, dict[str, float]] = {}
    for name in ("A_t", "Q_EM_over_s", "Q_nu_over_s"):
        require(np.all(low[name] > 0.0), f"nonpositive denominator in {name}")
        ratio = high[name] / low[name]
        reference = float(ratio[0])
        ratio_metrics[name] = {
            "ratio": reference,
            "max_relative_nonconstancy": float(np.max(np.abs(ratio / reference - 1.0))),
        }
        require(
            ratio_metrics[name]["max_relative_nonconstancy"] <= 1e-14,
            f"payload ratio is not pointwise constant: {name}",
        )
    return {"sha256": hashes, "ratio_metrics": ratio_metrics}


def compute(provider_root: Path) -> dict[str, Any]:
    cards_path = provider_root / "tables" / "DMDE_v099_blind_spectral_source_cards.json"
    require(cards_path.is_file(), f"missing source cards: {cards_path}")
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    require(isinstance(cards, list) and len(cards) == 2, "exactly two source cards required")
    require(tuple(card.get("blind_id") for card in cards) == EXPECTED_IDS, "blind-card order/identity mismatch")
    require(float(cards[0]["tau_s"]) == float(cards[1]["tau_s"]), "pair lifetime mismatch")
    require(float(cards[0]["m_mu_MeV"]) == float(cards[1]["m_mu_MeV"]), "pair muon-mass mismatch")

    payload_audit = inspect_payloads(provider_root, cards)
    amplitudes = {str(card["blind_id"]): source_amplitudes(card) for card in cards}
    a1, a2 = (amplitudes[blind_id] for blind_id in EXPECTED_IDS)

    r_nu = a2["nu_number_per_species"] / a1["nu_number_per_species"]
    r_em = a2["em_energy_MeV"] / a1["em_energy_MeV"]
    r_nu_energy = a2["nu_energy_MeV"] / a1["nu_energy_MeV"]
    r_parent = a2["parent_rest_energy_MeV"] / a1["parent_rest_energy_MeV"]
    du = math.log(r_nu)
    dv = math.log(r_em)
    rho = dv / du
    dparent = math.log(r_parent)
    require(abs(r_nu / r_nu_energy - 1.0) <= 2e-15, "neutrino number/energy ratios disagree")
    for blind_id in EXPECTED_IDS:
        amplitude = amplitudes[blind_id]
        require(
            abs(
                (amplitude["em_energy_MeV"] + amplitude["nu_energy_MeV"])
                / amplitude["parent_rest_energy_MeV"]
                - 1.0
            )
            <= 2e-15,
            f"parent-energy closure failure: {blind_id}",
        )
    require(abs(payload_audit["ratio_metrics"]["A_t"]["ratio"] / r_nu - 1.0) <= 2e-15, "A_t/card ratio mismatch")
    require(abs(payload_audit["ratio_metrics"]["Q_nu_over_s"]["ratio"] / r_nu - 1.0) <= 2e-15, "Q_nu/card ratio mismatch")
    require(abs(payload_audit["ratio_metrics"]["Q_EM_over_s"]["ratio"] / r_em - 1.0) <= 2e-15, "Q_EM/card ratio mismatch")

    precision = []
    for target in ELASTICITY_ERROR_TARGETS:
        # If each endpoint log-output error is bounded by eps, the worst-case
        # error of (ln O2-ln O1)/du is 2 eps/du.
        endpoint_log_error = 0.5 * target * du
        precision.append(
            {
                "pair_elasticity_absolute_error_target": target,
                "max_each_endpoint_log_output_error": endpoint_log_error,
                "max_each_endpoint_error_ppm_small_error_limit": endpoint_log_error * 1e6,
            }
        )

    detectability = []
    for elasticity in ELASTICITY_MAGNITUDES:
        for sigma_level in (3, 5):
            # Independent equal Gaussian log-output uncertainties sigma give
            # sd(log O2/O1)=sqrt(2)*sigma.
            per_endpoint_sigma = abs(elasticity) * du / (sigma_level * math.sqrt(2.0))
            detectability.append(
                {
                    "assumed_pair_averaged_neutrino_elasticity_abs": elasticity,
                    "sigma_level": sigma_level,
                    "max_each_endpoint_log_output_sigma": per_endpoint_sigma,
                    "max_each_endpoint_sigma_ppm_small_error_limit": per_endpoint_sigma * 1e6,
                }
            )

    completeness = 1.0 - math.exp(-18.0)
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "scope": "frozen-source geometry and numerical design only; no transport, weak-rate, BBN, or cosmological prediction",
        "input_identity": {
            "cards_path_relative_to_provider": str(cards_path.relative_to(provider_root)),
            "cards_sha256": sha256_file(cards_path),
            "payload_sha256": payload_audit["sha256"],
        },
        "common_frozen_values": {
            "tau_s": float(cards[0]["tau_s"]),
            "m_mu_MeV": float(cards[0]["m_mu_MeV"]),
            "cutoff_t_over_tau": 18.0,
            "active_completeness_1_minus_exp_minus_18": completeness,
        },
        "source_amplitudes_before_cutoff_completeness": amplitudes,
        "payload_pointwise_ratio_audit": payload_audit["ratio_metrics"],
        "log_source_geometry": {
            "nu_amplitude_ratio_high_over_low": r_nu,
            "em_amplitude_ratio_high_over_low": r_em,
            "delta_ln_nu_amplitude": du,
            "delta_ln_em_amplitude": dv,
            "parent_rest_energy_ratio_high_over_low": r_parent,
            "delta_ln_parent_rest_energy": dparent,
            "parent_log_contrast_per_nu_log_contrast": dparent / du,
            "em_to_nu_log_contrast_ratio_rho": rho,
            "nu_axis_suppression_factor_1_over_rho": 1.0 / rho,
            "pair_direction_angle_from_nu_axis_degrees": math.degrees(math.atan(rho)),
            "conditional_em_bias_bound_per_unit_em_elasticity": abs(rho),
        },
        "exact_response_identity": {
            "observable_requirement": "O(a,e)>0 and differentiable along the reduced frozen-source path; q_nu=1.3*m_mu*a and parent_energy=e+q_nu",
            "pair_estimator": "g_pair=[ln O(a2,e2)-ln O(a1,e1)]/delta_ln_nu",
            "identity": "g_pair=integral_0^1 [partial_ln_a ln O + rho*partial_ln_e ln O] ds",
            "conditional_bound": "if |partial_ln_e ln O|<=M_EM along the path, |g_pair-average(g_nu)|<=|rho|*M_EM",
            "warning": "The pair estimator is a path-averaged full neutrino-injection response, including the associated neutrino-energy/parent-density change; it is not automatically a local derivative, a weak-kernel-only response, or a DMDE abundance prediction.",
        },
        "orthogonal_diagnostic_design": {
            "physical_endpoints": {
                "P11": "(a1,e1) = 4Q7N",
                "P22": "(a2,e2) = 8M2K",
            },
            "optional_nonphysical_execution_canaries": {
                "P21": "(a2,e1): high neutrino amplitude, low EM amplitude",
                "P12": "(a1,e2): low neutrino amplitude, high EM amplitude",
            },
            "fixed_em_neutrino_secants": [
                "[ln O(P21)-ln O(P11)]/delta_ln_nu",
                "[ln O(P22)-ln O(P12)]/delta_ln_nu",
            ],
            "mixed_interaction_secant": "[ln O(P22)-ln O(P21)-ln O(P12)+ln O(P11)]/(delta_ln_nu*delta_ln_em)",
            "interpretation": "P21/P12 are execution diagnostics assembled from frozen amplitudes, not new physical branch points and not inputs to blinded scoring.",
            "conditioning_warning": "The actual EM contrast is only about 3.986 ppm; estimating an EM derivative from P11/P12 alone is numerically ill-conditioned.",
        },
        "worst_case_endpoint_precision_for_pair_elasticity": precision,
        "gaussian_detectability_design": detectability,
    }


def write_csv(path: Path, result: dict[str, Any]) -> None:
    geometry = result["log_source_geometry"]
    rows: list[dict[str, Any]] = []
    for item in result["worst_case_endpoint_precision_for_pair_elasticity"]:
        rows.append({"section": "worst_case_elasticity_accuracy", **item})
    for item in result["gaussian_detectability_design"]:
        rows.append({"section": "gaussian_detectability", **item})
    fieldnames = [
        "section",
        "pair_elasticity_absolute_error_target",
        "max_each_endpoint_log_output_error",
        "max_each_endpoint_error_ppm_small_error_limit",
        "assumed_pair_averaged_neutrino_elasticity_abs",
        "sigma_level",
        "max_each_endpoint_log_output_sigma",
        "max_each_endpoint_sigma_ppm_small_error_limit",
        "delta_ln_nu_amplitude",
        "delta_ln_em_amplitude",
        "rho",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            row.update(
                {
                    "delta_ln_nu_amplitude": geometry["delta_ln_nu_amplitude"],
                    "delta_ln_em_amplitude": geometry["delta_ln_em_amplitude"],
                    "rho": geometry["em_to_nu_log_contrast_ratio_rho"],
                }
            )
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-root", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = compute(args.provider_root.resolve())
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_bytes(canonical_json_bytes(result))
    write_csv(args.csv_out, result)
    print(
        "PASS",
        f"delta_ln_nu={result['log_source_geometry']['delta_ln_nu_amplitude']:.17g}",
        f"delta_ln_em={result['log_source_geometry']['delta_ln_em_amplitude']:.17g}",
        f"rho={result['log_source_geometry']['em_to_nu_log_contrast_ratio_rho']:.17g}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
