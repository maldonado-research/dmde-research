#!/usr/bin/env python3
"""Validate the DMDE v0.9.20 five-channel weak-rate closure.

This is an execution firewall, not an independent corrected weak-rate solver.
It supplies a neutron-lifetime-normalized finite-electron-mass Born lane for
all five canonical processes, exact process identities, late neutron-decay
normalization, direction-total normalization, and optional exported
momentum-integrand sum closure.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from dmde_v0920_causal_common import (
    ContractError,
    exact_keys,
    finite_float,
    load_json_object,
    sha256_file,
    valid_sha256,
)


SCHEMA_VERSION = "DMDE-WEAK-RATE-CAUSAL-CLOSURE-v0.9.20"
M_E_MEV = 0.51099895
DELTA_NP_MEV = 1.29333236
BORN_PROCESS_RELATIVE_BAND = 0.25
BORN_DIRECTION_TOTAL_RELATIVE_BAND = 0.10
LATE_DECAY_RELATIVE_TOLERANCE = 0.005
LATE_TEMPERATURE_MAX_MEV = 0.05
PROCESS_SUM_RTOL = 5e-10
PROCESS_SUM_ATOL_S_INV = 1e-14
BORN_FLOOR_RELATIVE_TO_PEAK = 1e-10
BORN_FLOOR_ABSOLUTE_S_INV = 1e-18
BORN_BLOCKING_CONVENTION = (
    "returned f_nue/f_nuebar for neutrino blocking; zero-chemical-potential "
    "Fermi-Dirac e-/e+ at T_gamma"
)

N_TO_P_LABELS = [
    "nu_e+n->p+e-",
    "e++n->p+nuebar",
    "n->p+e-+nuebar",
]
P_TO_N_LABELS = [
    "nuebar+p->n+e+",
    "e-+p->n+nue",
]
PROCESS_METRIC_NAMES = {
    N_TO_P_LABELS[0]: "nue_n_capture",
    N_TO_P_LABELS[1]: "eplus_n_capture",
    N_TO_P_LABELS[2]: "blocked_neutron_beta_decay",
    P_TO_N_LABELS[0]: "nuebar_p_capture",
    P_TO_N_LABELS[1]: "eminus_p_capture",
}

REQUIRED_NPZ = {
    "t_s",
    "T_gamma_MeV",
    "q_grid",
    "q_weights",
    "p_per_q_MeV",
    "f_nue",
    "f_nuebar",
    "neutron_lifetime_s",
    "lambda_n_to_p_s_inv",
    "lambda_p_to_n_s_inv",
    "lambda_n_to_p_process_s_inv",
    "lambda_p_to_n_process_s_inv",
}

INTEGRAND_ARRAYS = {
    "lambda_n_to_p_process_integrand_s_inv_per_q": (3, "lambda_n_to_p_process_s_inv"),
    "lambda_p_to_n_process_integrand_s_inv_per_q": (2, "lambda_p_to_n_process_s_inv"),
    "lambda_n_to_p_process_nongrid_s_inv": (3, "lambda_n_to_p_process_s_inv"),
    "lambda_p_to_n_process_nongrid_s_inv": (2, "lambda_p_to_n_process_s_inv"),
}

METADATA_KEYS = {
    "schema_version",
    "bridge_history_sha256",
    "weak_rate_production_callable",
    "weak_rate_code_sha256",
    "weak_rate_config_sha256",
    "n_to_p_process_labels",
    "p_to_n_process_labels",
    "born_normalization",
    "electron_positron_distribution",
    "born_processes_checked",
    "born_blocking_convention",
    "born_process_relative_band",
    "born_direction_total_relative_band",
    "born_non_negligible_floor_relative_to_peak",
    "born_non_negligible_floor_absolute_s_inv",
    "late_decay_relative_tolerance",
    "late_temperature_max_MeV",
    "momentum_integrands_present",
    "integrand_sum_relative_tolerance",
    "integrand_sum_absolute_tolerance_s_inv",
}


def _scalar(array: np.ndarray, *, label: str) -> float:
    value = np.asarray(array)
    if value.size != 1:
        raise ContractError(f"{label}: scalar required")
    return finite_float(value.reshape(-1)[0], label=label)


def _fermi_dirac(energy: np.ndarray, temperature: np.ndarray) -> np.ndarray:
    ratio = energy / temperature
    with np.errstate(over="ignore", invalid="ignore"):
        return np.where(ratio < 700.0, 1.0 / (np.exp(ratio) + 1.0), 0.0)


def _born_normalization(neutron_lifetime_s: float) -> tuple[float, float]:
    """Return I0 and A=(tau_n I0)^-1 using fixed Gauss-Legendre quadrature."""
    nodes, weights = np.polynomial.legendre.leggauss(256)
    energy = M_E_MEV + (DELTA_NP_MEV - M_E_MEV) * (nodes + 1.0) / 2.0
    denergy = (DELTA_NP_MEV - M_E_MEV) / 2.0
    momentum = np.sqrt(np.maximum(energy**2 - M_E_MEV**2, 0.0))
    integrand = energy * momentum * (DELTA_NP_MEV - energy) ** 2
    i0 = float(np.sum(weights * denergy * integrand))
    if not math.isfinite(i0) or i0 <= 0:
        raise ContractError("Born normalization integral is invalid")
    return i0, 1.0 / (neutron_lifetime_s * i0)


def compute_born_process_histories(
    q: np.ndarray,
    q_weights: np.ndarray,
    p_per_q: np.ndarray,
    temperature: np.ndarray,
    f_nue: np.ndarray,
    f_nuebar: np.ndarray,
    neutron_lifetime_s: float,
) -> tuple[dict[str, np.ndarray], float, float]:
    """Compute all five independent Born histories on the bridge quadrature.

    The integration variable ``p`` is the massless (anti)neutrino energy.
    Incoming neutrinos use the returned occupation. Outgoing neutrinos use
    that same returned state as a Pauli-blocking factor. Electrons and
    positrons use a zero-chemical-potential Fermi-Dirac distribution at
    ``T_gamma``. The common absolute normalization is fixed only by the
    declared neutron lifetime and the vacuum beta-decay integral ``I0``.
    """
    i0, normalization = _born_normalization(neutron_lifetime_s)
    p = p_per_q[:, None] * q[None, :]
    dp = p_per_q[:, None] * q_weights[None, :]
    temp = temperature[:, None]

    high_energy = p + DELTA_NP_MEV
    high_momentum = np.sqrt(np.maximum(high_energy**2 - M_E_MEV**2, 0.0))
    high_fd = _fermi_dirac(high_energy, temp)
    high_phase = p**2 * high_energy * high_momentum

    low_energy = p - DELTA_NP_MEV
    low_allowed = low_energy >= M_E_MEV
    low_momentum = np.sqrt(np.maximum(low_energy**2 - M_E_MEV**2, 0.0))
    low_fd = _fermi_dirac(np.maximum(low_energy, M_E_MEV), temp)
    low_phase = np.where(
        low_allowed,
        p**2 * low_energy * low_momentum,
        0.0,
    )

    decay_electron_energy = DELTA_NP_MEV - p
    decay_allowed = decay_electron_energy >= M_E_MEV
    decay_electron_momentum = np.sqrt(np.maximum(
        decay_electron_energy**2 - M_E_MEV**2, 0.0
    ))
    decay_electron_fd = _fermi_dirac(
        np.maximum(decay_electron_energy, M_E_MEV), temp
    )
    decay_phase = np.where(
        decay_allowed,
        p**2 * decay_electron_energy * decay_electron_momentum,
        0.0,
    )

    integrands = {
        N_TO_P_LABELS[0]: high_phase * f_nue * (1.0 - high_fd),
        N_TO_P_LABELS[1]: low_phase * low_fd * (1.0 - f_nuebar),
        N_TO_P_LABELS[2]: (
            decay_phase * (1.0 - decay_electron_fd) * (1.0 - f_nuebar)
        ),
        P_TO_N_LABELS[0]: low_phase * f_nuebar * (1.0 - low_fd),
        P_TO_N_LABELS[1]: high_phase * high_fd * (1.0 - f_nue),
    }
    histories = {
        label: normalization * np.sum(dp * integrand, axis=1)
        for label, integrand in integrands.items()
    }
    return histories, i0, normalization


def compute_born_capture_histories(
    q: np.ndarray,
    q_weights: np.ndarray,
    p_per_q: np.ndarray,
    temperature: np.ndarray,
    f_nue: np.ndarray,
    f_nuebar: np.ndarray,
    neutron_lifetime_s: float,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Compatibility wrapper for the two v0.9.19 capture sentinels."""
    histories, i0, normalization = compute_born_process_histories(
        q, q_weights, p_per_q, temperature, f_nue, f_nuebar,
        neutron_lifetime_s,
    )
    return (
        histories[N_TO_P_LABELS[0]], histories[P_TO_N_LABELS[0]],
        i0, normalization,
    )


def _validate_metadata(metadata: dict[str, Any], npz_path: Path, errors: list[str]) -> None:
    try:
        exact_keys(metadata, METADATA_KEYS, label="metadata")
    except ContractError as exc:
        errors.append(str(exc))
        return
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("metadata schema_version mismatch")
    if metadata.get("bridge_history_sha256") != sha256_file(npz_path):
        errors.append("metadata bridge_history_sha256 mismatch")
    for key in ("weak_rate_code_sha256", "weak_rate_config_sha256"):
        if not valid_sha256(metadata.get(key)):
            errors.append(f"metadata {key}: lowercase SHA-256 required")
    if not isinstance(metadata.get("weak_rate_production_callable"), str) or not metadata["weak_rate_production_callable"].strip():
        errors.append("metadata weak_rate_production_callable: nonempty string required")
    if metadata.get("n_to_p_process_labels") != N_TO_P_LABELS:
        errors.append("metadata n_to_p_process_labels: canonical ontology/order mismatch")
    if metadata.get("p_to_n_process_labels") != P_TO_N_LABELS:
        errors.append("metadata p_to_n_process_labels: canonical ontology/order mismatch")
    if metadata.get("born_processes_checked") != N_TO_P_LABELS + P_TO_N_LABELS:
        errors.append("metadata born_processes_checked: all five canonical labels/order required")
    exact_values = {
        "born_normalization": "A=(tau_n*I0)^-1",
        "electron_positron_distribution": "zero-chemical-potential Fermi-Dirac at T_gamma",
        "born_blocking_convention": BORN_BLOCKING_CONVENTION,
        "born_process_relative_band": BORN_PROCESS_RELATIVE_BAND,
        "born_direction_total_relative_band": BORN_DIRECTION_TOTAL_RELATIVE_BAND,
        "born_non_negligible_floor_relative_to_peak": BORN_FLOOR_RELATIVE_TO_PEAK,
        "born_non_negligible_floor_absolute_s_inv": BORN_FLOOR_ABSOLUTE_S_INV,
        "late_decay_relative_tolerance": LATE_DECAY_RELATIVE_TOLERANCE,
        "late_temperature_max_MeV": LATE_TEMPERATURE_MAX_MEV,
        "integrand_sum_relative_tolerance": PROCESS_SUM_RTOL,
        "integrand_sum_absolute_tolerance_s_inv": PROCESS_SUM_ATOL_S_INV,
    }
    for key, wanted in exact_values.items():
        if metadata.get(key) != wanted:
            errors.append(f"metadata {key}: exact v0.9.20 contract value required")
    if not isinstance(metadata.get("momentum_integrands_present"), bool):
        errors.append("metadata momentum_integrands_present: boolean required")


def _masked_relative_error(actual: np.ndarray, reference: np.ndarray) -> tuple[float, int, float]:
    peak = float(np.max(reference))
    floor = max(BORN_FLOOR_ABSOLUTE_S_INV, peak * BORN_FLOOR_RELATIVE_TO_PEAK)
    mask = reference >= floor
    if not np.any(mask):
        return math.inf, 0, floor
    rel = np.abs(actual[mask] / reference[mask] - 1.0)
    return float(np.max(rel)), int(np.count_nonzero(mask)), floor


def validate_weak_rate_closure(npz_path: Path | str, metadata_path: Path | str) -> dict[str, Any]:
    npz_path = Path(npz_path)
    metadata_path = Path(metadata_path)
    errors: list[str] = []
    metrics: dict[str, Any] = {}

    if not npz_path.is_file() or npz_path.is_symlink():
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": ["bridge NPZ missing or unsafe"], "metrics": {}}
    if not metadata_path.is_file() or metadata_path.is_symlink():
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": ["weak-rate metadata missing or unsafe"], "metrics": {}}
    try:
        metadata = load_json_object(metadata_path, label="weak-rate metadata")
    except ContractError as exc:
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": [str(exc)], "metrics": {}}
    _validate_metadata(metadata, npz_path, errors)

    try:
        data = np.load(npz_path, allow_pickle=False)
    except Exception as exc:
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors + [f"NPZ load failure: {exc}"], "metrics": {}}
    missing = sorted(REQUIRED_NPZ - set(data.files))
    if missing:
        data.close()
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors + ["missing required NPZ fields: " + ", ".join(missing)], "metrics": {}}

    try:
        t = np.asarray(data["t_s"], dtype=float)
        temperature = np.asarray(data["T_gamma_MeV"], dtype=float)
        q = np.asarray(data["q_grid"], dtype=float)
        q_weights = np.asarray(data["q_weights"], dtype=float)
        p_per_q = np.asarray(data["p_per_q_MeV"], dtype=float)
        f_nue = np.asarray(data["f_nue"], dtype=float)
        f_nuebar = np.asarray(data["f_nuebar"], dtype=float)
        tau_n = _scalar(data["neutron_lifetime_s"], label="neutron_lifetime_s")
        rate_np = np.asarray(data["lambda_n_to_p_s_inv"], dtype=float)
        rate_pn = np.asarray(data["lambda_p_to_n_s_inv"], dtype=float)
        process_np = np.asarray(data["lambda_n_to_p_process_s_inv"], dtype=float)
        process_pn = np.asarray(data["lambda_p_to_n_process_s_inv"], dtype=float)
    except Exception as exc:
        data.close()
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors + [f"array parse failure: {exc}"], "metrics": metrics}

    nt, nq = len(t), len(q)
    vector_fields = {
        "t_s": t,
        "T_gamma_MeV": temperature,
        "p_per_q_MeV": p_per_q,
        "lambda_n_to_p_s_inv": rate_np,
        "lambda_p_to_n_s_inv": rate_pn,
    }
    for key, values in vector_fields.items():
        if values.shape != (nt,) or not np.all(np.isfinite(values)):
            errors.append(f"{key}: finite shape (Nt,) required")
    if q.shape != (nq,) or q_weights.shape != (nq,) or nq < 2:
        errors.append("q_grid/q_weights: matching one-dimensional grids with at least two nodes required")
    elif not np.all(np.isfinite(q)) or not np.all(np.isfinite(q_weights)) or np.any(q <= 0) or np.any(q_weights <= 0) or np.any(np.diff(q) <= 0):
        errors.append("q_grid/q_weights: positive finite strictly increasing grid and positive weights required")
    if nt < 2 or np.any(np.diff(t) <= 0):
        errors.append("t_s: at least two strictly increasing nodes required")
    if np.any(temperature <= 0) or np.any(p_per_q <= 0):
        errors.append("T_gamma_MeV and p_per_q_MeV must be positive")
    for key, values in (("f_nue", f_nue), ("f_nuebar", f_nuebar)):
        if values.shape != (nt, nq) or not np.all(np.isfinite(values)) or np.any(values < 0) or np.any(values > 1):
            errors.append(f"{key}: finite occupation array in [0,1] with shape (Nt,Nq) required")
    if process_np.shape != (nt, 3) or process_pn.shape != (nt, 2):
        errors.append("canonical process arrays must have shapes (Nt,3) and (Nt,2)")
    if not (800.0 < tau_n < 1000.0):
        errors.append("neutron_lifetime_s broad-range failure")
    for key, values in (("lambda_n_to_p", rate_np), ("lambda_p_to_n", rate_pn), ("lambda_n_to_p_process", process_np), ("lambda_p_to_n_process", process_pn)):
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            errors.append(f"{key}: finite nonnegative values required")

    if not errors:
        for label, total, process in (("n_to_p", rate_np, process_np), ("p_to_n", rate_pn, process_pn)):
            residual = np.abs(total - np.sum(process, axis=1))
            ceiling = PROCESS_SUM_ATOL_S_INV + PROCESS_SUM_RTOL * np.abs(total)
            metrics[f"{label}_process_sum_max_scaled_residual"] = float(np.max(residual / np.maximum(ceiling, 1e-300)))
            if np.any(residual > ceiling):
                errors.append(f"{label}: canonical process columns do not sum to total")

    if not errors:
        born, i0, normalization = compute_born_process_histories(
            q, q_weights, p_per_q, temperature, f_nue, f_nuebar, tau_n
        )
        metrics.update({
            "born_I0_MeV5": i0,
            "born_A_s_inv_MeV_minus5": normalization,
        })
        process_columns = {
            N_TO_P_LABELS[0]: process_np[:, 0],
            N_TO_P_LABELS[1]: process_np[:, 1],
            N_TO_P_LABELS[2]: process_np[:, 2],
            P_TO_N_LABELS[0]: process_pn[:, 0],
            P_TO_N_LABELS[1]: process_pn[:, 1],
        }
        for label in N_TO_P_LABELS + P_TO_N_LABELS:
            metric_name = PROCESS_METRIC_NAMES[label]
            relative_error, compared_points, floor = _masked_relative_error(
                process_columns[label], born[label]
            )
            metrics.update({
                f"born_{metric_name}_peak_s_inv": float(np.max(born[label])),
                f"born_{metric_name}_non_negligible_floor_s_inv": floor,
                f"born_{metric_name}_compared_points": compared_points,
                f"born_{metric_name}_max_relative_error": relative_error,
            })
            if compared_points == 0 or relative_error > BORN_PROCESS_RELATIVE_BAND:
                errors.append(
                    f"canonical {label} column fails independent Born 25% process band"
                )

        # This tighter lane catches common scaling of otherwise self-consistent
        # process columns because its absolute normalization is fixed by tau_n.
        for direction, actual, labels in (
            ("n_to_p", rate_np, N_TO_P_LABELS),
            ("p_to_n", rate_pn, P_TO_N_LABELS),
        ):
            reference = sum((born[label] for label in labels), np.zeros(nt))
            relative_error, compared_points, floor = _masked_relative_error(
                actual, reference
            )
            metrics.update({
                f"born_{direction}_total_peak_s_inv": float(np.max(reference)),
                f"born_{direction}_total_non_negligible_floor_s_inv": floor,
                f"born_{direction}_total_compared_points": compared_points,
                f"born_{direction}_total_max_relative_error": relative_error,
            })
            if compared_points == 0 or relative_error > BORN_DIRECTION_TOTAL_RELATIVE_BAND:
                errors.append(
                    f"canonical {direction} total fails independent Born 10% direction-total band"
                )

        late = temperature <= LATE_TEMPERATURE_MAX_MEV
        metrics["late_decay_compared_points"] = int(np.count_nonzero(late))
        if not np.any(late):
            errors.append("no history nodes satisfy the canonical late-decay temperature window")
        else:
            late_rel = np.abs(process_np[late, 2] * tau_n - 1.0)
            metrics["late_free_neutron_decay_max_relative_error"] = float(np.max(late_rel))
            if np.any(late_rel > LATE_DECAY_RELATIVE_TOLERANCE):
                errors.append("canonical free-neutron-decay column fails late 0.5% lifetime gate")

    optional_present = {key for key in INTEGRAND_ARRAYS if key in data.files}
    integrands_declared = metadata.get("momentum_integrands_present") is True
    if integrands_declared and optional_present != set(INTEGRAND_ARRAYS):
        errors.append("momentum integrands declared present but required all-or-none NPZ fields are missing")
    if optional_present and optional_present != set(INTEGRAND_ARRAYS):
        errors.append("partial momentum-integrand field set is forbidden")
    if optional_present and not integrands_declared:
        errors.append("momentum-integrand arrays present but metadata declares them absent")
    if optional_present == set(INTEGRAND_ARRAYS):
        for direction, nproc, process_key, integrand_key, nongrid_key in (
            ("n_to_p", 3, "lambda_n_to_p_process_s_inv", "lambda_n_to_p_process_integrand_s_inv_per_q", "lambda_n_to_p_process_nongrid_s_inv"),
            ("p_to_n", 2, "lambda_p_to_n_process_s_inv", "lambda_p_to_n_process_integrand_s_inv_per_q", "lambda_p_to_n_process_nongrid_s_inv"),
        ):
            integrand = np.asarray(data[integrand_key], dtype=float)
            nongrid = np.asarray(data[nongrid_key], dtype=float)
            process = process_np if direction == "n_to_p" else process_pn
            if integrand.shape != (nt, nproc, nq) or nongrid.shape != (nt, nproc):
                errors.append(f"{direction}: integrand/nongrid shape mismatch")
                continue
            if not np.all(np.isfinite(integrand)) or not np.all(np.isfinite(nongrid)):
                errors.append(f"{direction}: integrand/nongrid values must be finite")
                continue
            reconstructed = np.sum(integrand * q_weights[None, None, :], axis=2) + nongrid
            residual = np.abs(reconstructed - process)
            ceiling = PROCESS_SUM_ATOL_S_INV + PROCESS_SUM_RTOL * np.abs(process)
            metrics[f"{direction}_integrand_sum_max_scaled_residual"] = float(np.max(residual / np.maximum(ceiling, 1e-300)))
            if np.any(residual > ceiling):
                errors.append(f"{direction}: momentum-integrand sum closure failed")
    data.close()

    return {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bridge_npz")
    parser.add_argument("weak_rate_metadata_json")
    parser.add_argument("--out-json")
    args = parser.parse_args()
    result = validate_weak_rate_closure(args.bridge_npz, args.weak_rate_metadata_json)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out_json:
        Path(args.out_json).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
