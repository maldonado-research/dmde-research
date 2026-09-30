#!/usr/bin/env python3
"""Validate a source-frozen DMDE v0.9.20 spectral-to-BBN bridge draft.

The validator checks identity, source-history closure, endpoint coverage,
thermal and Michel quadrature through fifth order, two Born kinematic capture
proxies, broad rate/Hubble sanity, and machine-readable provenance.  It is an
execution firewall, not an independent neutrino-transport or BBN solver.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np

from dmde_v0920_common import (
    BRIDGE_SCHEMA, CARD_SCHEMA, PACKAGE, PAYLOAD_SCHEMA, close_float,
    contains_marker, is_placeholder, load_expected, norm, sha256_file,
    valid_sha256, valid_utc,
)

M3_EXACT = 7 * math.pi**4 / 120
M_E_MEV = 0.51099895
DELTA_NP_MEV = 1.29333236
HBAR_MEV_S = 6.582119569e-22
MPL_MEV = 1.220890e22
GSTAR_EARLY = 10.75

NPZ_MAX_ARCHIVE_BYTES = 1 << 30
NPZ_MAX_MEMBERS = 256
NPZ_MAX_TOTAL_UNCOMPRESSED_BYTES = 2 << 30
NPZ_MAX_COMPRESSION_RATIO = 1000.0
NPZ_MAX_GRID_CELLS = 50_000_000
NPZ_MEMBER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.npy")

THRESHOLDS = {
    "thermal_M3_abs_relerr_max": 5e-3,
    "initial_distribution_M3_abs_relerr_max": 5e-3,
    "michel_Ek_abs_relerr_max": 5e-3,
    "source_rhs_Ek_abs_relerr_max": 5e-3,
    "source_rhs_flavor_pair_relerr_max": 5e-10,
    "capture_proxy_abs_relerr_max": 5e-3,
    "source_history_relerr_max": 5e-10,
    "source_integral_relerr_max": 5e-5,
    "source_rhs_shape_weighted_l1_max": 5e-4,
    "source_rhs_shape_cdf_sup_max": 5e-4,
    "source_rhs_shape_peak_scaled_max": 5e-3,
    "source_rhs_time_integral_relerr_max": 5e-5,
    "initial_fd_weighted_l1_max": 5e-3,
    "initial_fd_cdf_sup_max": 5e-3,
    "state_mapping_weighted_l1_max": 5e-10,
    "state_mapping_peak_scaled_max": 5e-10,
    "stepper_response_weighted_l1_max": 5e-3,
    "stepper_response_moment_relerr_max": 5e-3,
    "stepper_halving_weighted_l1_max": 5e-3,
    "stepper_halving_moment_relerr_max": 5e-3,
    "source_rhs_zero_peak_rel_ceiling": 1e-14,
    "hubble_scale_factor_integral_relerr_max": 5e-3,
    "occupancy_tolerance": 1e-8,
    "T_start_min_MeV": 3.0,
    "T_end_max_MeV": 0.05,
    "t_end_min_s": 500.0,
    "endpoint_rel_margin_min": -1e-10,
}

REQ_SCALAR_TEXT = [
    "schema_version", "blind_id", "source_payload_sha256",
    "source_card_version", "source_payload_schema", "source_package_version",
    "source_card_json_sha256", "source_payload_manifest_sha256",
    "source_payload_schema_document_sha256",
]
REQ_SCALAR_FLOAT = [
    "source_tau_s", "source_m_mu_MeV", "source_mass_MeV", "source_Y0",
    "source_epsilon", "source_B_mumu",
    "source_B_ee_plus_EMlike_neutral_effective", "source_native_muon_multiplicity",
    "source_native_pion_multiplicity", "source_f_EM_integrated", "source_f_nu_integrated",
    "source_lifetime_factor", "neutron_lifetime_s",
    "Yp_model", "DH_x1e5_model", "Neff_CMB_model",
]
REQ_1D = [
    "t_s", "scale_factor", "T_gamma_MeV", "q_grid", "q_weights",
    "p_per_q_MeV", "source_dYdt_s_inv", "source_muon_pair_dYdt_s_inv",
    "source_Q_EM_over_s_MeV_s_inv", "source_Q_nu_over_s_MeV_s_inv",
    "source_Q_pi_charged_over_s_MeV_s_inv",
    "lambda_n_to_p_s_inv", "lambda_p_to_n_s_inv", "H_s_inv",
    "state_normalization_density_MeV3",
]
REQ_2D = [
    "f_nue", "f_nuebar", "f_numu", "f_numubar", "f_nutau", "f_nutaubar",
]
REQ_SOURCE_2D = [
    "source_rhs_nue_dYdt_dq_s_inv", "source_rhs_nuebar_dYdt_dq_s_inv",
    "source_rhs_numu_dYdt_dq_s_inv", "source_rhs_numubar_dYdt_dq_s_inv",
    "source_rhs_nutau_dYdt_dq_s_inv", "source_rhs_nutaubar_dYdt_dq_s_inv",
]
STATE_SPECIES = ("nue", "nuebar", "numu", "numubar", "nutau", "nutaubar")
SOURCE_ACTIVE_SPECIES = ("nue", "nuebar", "numu", "numubar")
CANONICAL_N_TO_P_LABELS = [
    "nu_e+n->p+e-", "e++n->p+nuebar", "n->p+e-+nuebar",
]
CANONICAL_P_TO_N_LABELS = [
    "nuebar+p->n+e+", "e-+p->n+nue",
]
REQ_STATE_2D = [f"state_dYdq_{species}" for species in STATE_SPECIES]
STEPPER_TARGET_T_OVER_TAU = np.asarray((0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0))
REQ_STEPPER_1D = [
    "source_stepper_target_t_over_tau", "source_stepper_time_index",
    "source_stepper_sample_t_s", "source_stepper_h_s", "source_stepper_h2_s",
]
REQ_STEPPER_2D = [
    f"source_stepper_{mode}_state_dYdq_{species}"
    for mode in ("initial", "on_h", "off_h", "on_h2", "off_h2")
    for species in STATE_SPECIES
]
REQ_PROCESS_2D = ["lambda_n_to_p_process_s_inv", "lambda_p_to_n_process_s_inv"]
META_REQUIRED = [
    "schema_version", "blind_id", "source_payload_sha256",
    "source_card_version", "source_payload_schema", "source_package_version",
    "source_epsilon", "source_B_ee_plus_EMlike_neutral_effective",
    "source_card_json_sha256", "source_payload_manifest_sha256",
    "source_payload_schema_document_sha256",
    "bridge_history_sha256", "run_role", "backend_family", "backend_name",
    "backend_version_or_commit", "backend_environment",
    "spectral_source_treatment", "collision_treatment", "oscillation_treatment",
    "momentum_grid_description", "momentum_coordinate_kind",
    "momentum_coordinate_definition", "quadrature_weight_definition",
    "physical_momentum_definition", "time_origin_definition",
    "neutrino_antineutrino_convention", "source_mapping_description",
    "source_endpoint_implementation", "source_rhs_stage", "source_rhs_units",
    "source_rhs_export_method", "source_rhs_production_callable",
    "source_rhs_adapter", "source_rhs_impulse_test_command", "weak_rate_processes",
    "state_dYdq_definition", "state_normalization_density_definition",
    "state_export_method", "transport_stepper_production_callable",
    "transport_stepper_source_toggle", "operator_probe_command",
    "source_stepper_witness_method", "source_stepper_response_definition",
    "source_stepper_target_policy", "source_stepper_state_units",
    "source_stepper_initial_state_definition",
    "weak_rate_production_callable", "weak_rate_canonical_process_map",
    "weak_rate_born_sentinel_definition", "bbn_consumption_canary_command",
    "weak_rate_corrections", "background_to_bbn_bridge", "nuclear_rate_set",
    "n_to_p_process_labels", "p_to_n_process_labels",
    "interpolation_policy", "extrapolation_policy", "production_or_synthetic",
    "generated_utc",
]


def _npz_preflight(path: Path) -> tuple[list[str], dict[str, object]]:
    """Bound and inspect an untrusted NPZ before NumPy allocates its arrays."""
    errors: list[str] = []
    metrics: dict[str, object] = {}
    if path.is_symlink():
        return ["NPZ preflight: symbolic links are forbidden"], metrics
    if path.suffix.lower() != ".npz":
        errors.append("NPZ preflight: filename must end in .npz")
    try:
        archive_bytes = path.stat().st_size
    except OSError as exc:
        return errors + [f"NPZ preflight: stat failure: {exc}"], metrics
    metrics["npz_archive_bytes"] = archive_bytes
    if archive_bytes > NPZ_MAX_ARCHIVE_BYTES:
        errors.append("NPZ preflight: archive exceeds 1 GiB ceiling")
        return errors, metrics
    try:
        with path.open("rb") as handle:
            prefix = handle.read(4)
            if archive_bytes >= 22:
                handle.seek(-22, 2)
                end_record = handle.read(22)
            else:
                end_record = b""
        if prefix != b"PK\x03\x04":
            errors.append("NPZ preflight: canonical ZIP must start with a local-file header")
        if len(end_record) != 22 or end_record[:4] != b"PK\x05\x06" or end_record[-2:] != b"\x00\x00":
            errors.append("NPZ preflight: trailing, prefixed, commented, or noncanonical ZIP framing")
    except OSError as exc:
        return errors + [f"NPZ preflight: framing read failure: {exc}"], metrics

    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            metrics["npz_member_count"] = len(infos)
            if archive.comment:
                errors.append("NPZ preflight: archive comment is forbidden")
            if not infos:
                errors.append("NPZ preflight: archive has no members")
            if len(infos) > NPZ_MAX_MEMBERS:
                errors.append("NPZ preflight: member-count ceiling exceeded")

            seen_names: set[str] = set()
            total_uncompressed = 0
            total_compressed = 0
            max_ratio = 0.0
            headers: dict[str, tuple[tuple[int, ...], np.dtype]] = {}
            for info in infos:
                name = info.filename
                normalized_name = unicodedata.normalize("NFC", name).casefold()
                posix = PurePosixPath(name)
                unsafe = (
                    not name or "\x00" in name or "\\" in name or posix.is_absolute()
                    or any(part in {"", ".", ".."} for part in posix.parts)
                )
                if unsafe:
                    errors.append(f"NPZ preflight: unsafe member path: {name!r}")
                if normalized_name in seen_names:
                    errors.append(f"NPZ preflight: duplicate/colliding member name: {name!r}")
                seen_names.add(normalized_name)
                if info.is_dir() or len(posix.parts) != 1 or not NPZ_MEMBER_RE.fullmatch(name):
                    errors.append(f"NPZ preflight: noncanonical member name: {name!r}")
                mode = (info.external_attr >> 16) & 0xFFFF
                if mode and stat.S_ISLNK(mode):
                    errors.append(f"NPZ preflight: symbolic-link member forbidden: {name!r}")
                if info.flag_bits & 0x1:
                    errors.append(f"NPZ preflight: encrypted member forbidden: {name!r}")
                if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    errors.append(f"NPZ preflight: unsupported compression method: {name!r}")
                if info.comment:
                    errors.append(f"NPZ preflight: member comment forbidden: {name!r}")
                total_uncompressed += info.file_size
                total_compressed += info.compress_size
                ratio = info.file_size / max(info.compress_size, 1)
                max_ratio = max(max_ratio, ratio)
                if ratio > NPZ_MAX_COMPRESSION_RATIO:
                    errors.append(f"NPZ preflight: member compression-ratio ceiling exceeded: {name!r}")

            metrics["npz_total_uncompressed_bytes"] = total_uncompressed
            metrics["npz_max_member_compression_ratio"] = max_ratio
            archive_ratio = total_uncompressed / max(total_compressed, 1)
            metrics["npz_archive_compression_ratio"] = archive_ratio
            if total_uncompressed > NPZ_MAX_TOTAL_UNCOMPRESSED_BYTES:
                errors.append("NPZ preflight: total uncompressed size exceeds 2 GiB ceiling")
            if archive_ratio > NPZ_MAX_COMPRESSION_RATIO:
                errors.append("NPZ preflight: archive compression-ratio ceiling exceeded")

            if not errors:
                bad_member = archive.testzip()
                if bad_member is not None:
                    errors.append(f"NPZ preflight: CRC failure in member: {bad_member!r}")

            if not errors:
                for info in infos:
                    key = info.filename[:-4]
                    try:
                        with archive.open(info, "r") as member:
                            version = np.lib.format.read_magic(member)
                            if version == (1, 0):
                                shape, _, dtype = np.lib.format.read_array_header_1_0(member)
                            elif version == (2, 0):
                                shape, _, dtype = np.lib.format.read_array_header_2_0(member)
                            else:
                                raise ValueError(f"unsupported NPY format version {version}")
                            header_bytes = member.tell()
                        dtype = np.dtype(dtype)
                        if dtype.hasobject:
                            errors.append(f"NPZ preflight: object/pickle dtype forbidden: {info.filename!r}")
                        expected_member_bytes = header_bytes + math.prod(shape) * dtype.itemsize
                        if expected_member_bytes != info.file_size:
                            errors.append(f"NPZ preflight: NPY payload length mismatch: {info.filename!r}")
                        headers[key] = (tuple(shape), dtype)
                    except Exception as exc:
                        errors.append(f"NPZ preflight: invalid NPY header for {info.filename!r}: {exc}")

            required = (
                REQ_SCALAR_TEXT + REQ_SCALAR_FLOAT + REQ_1D
                + REQ_2D + REQ_SOURCE_2D + REQ_STATE_2D
                + REQ_STEPPER_1D + REQ_STEPPER_2D + REQ_PROCESS_2D
            )
            for key in required:
                if key not in headers and not errors:
                    errors.append(f"NPZ preflight: missing array member: {key}")
            if not errors:
                for key in REQ_SCALAR_TEXT + REQ_SCALAR_FLOAT:
                    shape, _ = headers[key]
                    if math.prod(shape) != 1:
                        errors.append(f"NPZ preflight: {key} is not scalar")
                t_shape = headers["t_s"][0]
                q_shape = headers["q_grid"][0]
                if len(t_shape) != 1 or len(q_shape) != 1:
                    errors.append("NPZ preflight: t_s and q_grid must be one-dimensional")
                else:
                    nt, nq = t_shape[0], q_shape[0]
                    grid_cells = nt * nq
                    metrics.update({
                        "npz_header_Nt": nt,
                        "npz_header_Nq": nq,
                        "npz_header_Nt_times_Nq": grid_cells,
                    })
                    if nt < 1 or nq < 1:
                        errors.append("NPZ preflight: t_s and q_grid must be nonempty")
                    if grid_cells > NPZ_MAX_GRID_CELLS:
                        errors.append("NPZ preflight: Nt*Nq exceeds 50-million-cell ceiling")
                    for key in REQ_1D:
                        expected_shape = (nq,) if key in {"q_grid", "q_weights"} else (nt,)
                        if headers[key][0] != expected_shape:
                            errors.append(f"NPZ preflight: {key} has wrong shape")
                    for key in REQ_2D + REQ_SOURCE_2D + REQ_STATE_2D:
                        if headers[key][0] != (nt, nq):
                            errors.append(f"NPZ preflight: {key} has wrong shape")
                    for key in REQ_STEPPER_1D:
                        if headers[key][0] != (len(STEPPER_TARGET_T_OVER_TAU),):
                            errors.append(f"NPZ preflight: {key} has wrong shape")
                    for key in REQ_STEPPER_2D:
                        if headers[key][0] != (len(STEPPER_TARGET_T_OVER_TAU), nq):
                            errors.append(f"NPZ preflight: {key} has wrong shape")
                    for key in REQ_PROCESS_2D:
                        shape = headers[key][0]
                        if len(shape) != 2 or shape[0] != nt or shape[1] < 2:
                            errors.append(f"NPZ preflight: {key} has wrong shape")
                        elif math.prod(shape) > NPZ_MAX_GRID_CELLS:
                            errors.append(f"NPZ preflight: {key} exceeds 50-million-cell ceiling")
    except zipfile.BadZipFile as exc:
        errors.append(f"NPZ preflight: not a valid ZIP/NPZ archive: {exc}")
    except (OSError, RuntimeError) as exc:
        errors.append(f"NPZ preflight: archive read failure: {exc}")
    return errors, metrics


def _scalar(array):
    value = np.asarray(array)
    if value.size != 1:
        raise ValueError("not scalar")
    item = value.reshape(-1)[0]
    return item.item() if hasattr(item, "item") else item


def _strict_increasing(values) -> bool:
    return bool(np.all(np.diff(np.asarray(values, dtype=float)) > 0))


def _mostly_decreasing(values) -> bool:
    differences = np.diff(np.asarray(values, dtype=float))
    return bool(len(differences) and np.mean(differences <= 1e-12) >= 0.98)


def _time_weights(t: np.ndarray) -> np.ndarray:
    weights = np.zeros_like(t, dtype=float)
    delta = np.diff(t)
    weights[:-1] += delta / 2
    weights[1:] += delta / 2
    return weights


def _weighted_shape_metrics(
    actual: np.ndarray,
    expected: np.ndarray,
    weights: np.ndarray,
) -> tuple[float, float, float]:
    """Return expected-mass-normalized L1, normalized-CDF sup, and peak residual.

    The caller supplies the physical measure in ``weights``.  Comparing the
    canonical and returned arrays on the same nodes prevents a continuum
    reference from hiding a discrete source-shape or initial-state defect.
    """
    actual = np.asarray(actual, dtype=float)
    expected = np.asarray(expected, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if actual.ndim != 1 or expected.shape != actual.shape or weights.shape != actual.shape:
        raise ValueError("weighted-shape arrays must be matching one-dimensional vectors")
    if not (
        np.all(np.isfinite(actual)) and np.all(np.isfinite(expected))
        and np.all(np.isfinite(weights))
    ):
        return math.inf, math.inf, math.inf
    if np.any(weights < 0) or np.any(expected < 0):
        return math.inf, math.inf, math.inf
    expected_weighted = weights * expected
    actual_weighted = weights * actual
    expected_mass = float(np.sum(expected_weighted))
    actual_mass = float(np.sum(actual_weighted))
    expected_peak = float(np.max(np.abs(expected)))
    if expected_mass <= 0 or actual_mass <= 0 or expected_peak <= 0:
        return math.inf, math.inf, math.inf
    weighted_l1 = float(np.sum(weights * np.abs(actual - expected)) / expected_mass)
    expected_cdf = np.cumsum(expected_weighted) / expected_mass
    actual_cdf = np.cumsum(actual_weighted) / actual_mass
    cdf_sup = float(np.max(np.abs(actual_cdf - expected_cdf)))
    peak_scaled = float(np.max(np.abs(actual - expected)) / expected_peak)
    return weighted_l1, cdf_sup, peak_scaled


def _half_open_source_masks(
    t: np.ndarray,
    tau: float,
    lifetime_factor: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return the exact frozen source domain ``[0, lifetime_factor*tau)``."""
    times = np.asarray(t, dtype=float)
    cutoff = float(tau) * float(lifetime_factor)
    active = (times >= 0.0) & (times < cutoff)
    post_cutoff = times >= cutoff
    return active, post_cutoff, cutoff


def _expected_source_rhs(
    q: np.ndarray,
    p_per_q: np.ndarray,
    source_expected: np.ndarray,
    branch: float,
    m_mu: float,
    species: str,
) -> np.ndarray:
    """Canonical discrete ``dY/(dt dq)`` for one stopped-muon species."""
    q = np.asarray(q, dtype=float)
    p_per_q = np.asarray(p_per_q, dtype=float)
    source_expected = np.asarray(source_expected, dtype=float)
    if species in {"nutau", "nutaubar"}:
        return np.zeros((len(source_expected), len(q)), dtype=float)
    michel_label = "nue" if species in {"nue", "nuebar"} else "numu"
    p = p_per_q[:, None] * q[None, :]
    density_dp = _michel_density(p, michel_label, m_mu)
    return branch * source_expected[:, None] * density_dp * p_per_q[:, None]


def _nearest_target_indices(
    t: np.ndarray,
    tau: float,
    targets: np.ndarray = STEPPER_TARGET_T_OVER_TAU,
) -> np.ndarray:
    """Select nearest rows deterministically; NumPy resolves ties to the first."""
    ratios = np.asarray(t, dtype=float) / float(tau)
    targets = np.asarray(targets, dtype=float)
    return np.asarray([int(np.argmin(np.abs(ratios - target))) for target in targets], dtype=int)


def _moment(
    values_dYdq: np.ndarray,
    q: np.ndarray,
    q_weights: np.ndarray,
    p_per_q: float,
    order: int,
) -> float:
    return float(
        float(p_per_q) ** order
        * np.sum(np.asarray(q_weights) * np.asarray(values_dYdq) * np.asarray(q) ** order)
    )


def _state_dydq_from_f(
    distribution: np.ndarray,
    q: np.ndarray,
    p_per_q: np.ndarray,
    normalization_density: np.ndarray,
) -> np.ndarray:
    distribution = np.asarray(distribution, dtype=float)
    q = np.asarray(q, dtype=float)
    p_per_q = np.asarray(p_per_q, dtype=float)
    normalization_density = np.asarray(normalization_density, dtype=float)
    if distribution.shape != (len(p_per_q), len(q)):
        raise ValueError("distribution shape is inconsistent with state coordinates")
    if normalization_density.shape != p_per_q.shape or np.any(normalization_density <= 0):
        raise ValueError("state normalization density must be a positive Nt vector")
    return distribution * (
        q[None, :] ** 2 * p_per_q[:, None] ** 3
        / (2 * math.pi**2 * normalization_density[:, None])
    )


def _paired_stepper_response(
    source_on_state: np.ndarray,
    source_off_state: np.ndarray,
    step_s: np.ndarray,
) -> np.ndarray:
    source_on_state = np.asarray(source_on_state, dtype=float)
    source_off_state = np.asarray(source_off_state, dtype=float)
    step_s = np.asarray(step_s, dtype=float)
    if source_on_state.shape != source_off_state.shape or source_on_state.ndim != 2:
        raise ValueError("paired stepper states must have matching two-dimensional shapes")
    if step_s.shape != (source_on_state.shape[0],) or np.any(step_s <= 0):
        raise ValueError("stepper step vector must be positive with one value per witness row")
    return (source_on_state - source_off_state) / step_s[:, None]


def _michel_moment_x(label: str, k: int) -> float:
    if label == "nue":
        return 12.0 / ((k + 3) * (k + 4))
    return 2.0 * (k + 6) / ((k + 3) * (k + 4))


def _michel_density(p: np.ndarray, label: str, m_mu: float) -> np.ndarray:
    if label == "nue":
        result = 96 * p**2 * (1 - 2 * p / m_mu) / m_mu**3
    else:
        result = 48 * p**2 * (1 - 4 * p / (3 * m_mu)) / m_mu**3
    return np.where((p >= 0) & (p <= m_mu / 2), result, 0.0)


def _capture_weight(p: np.ndarray, kind: str) -> np.ndarray:
    electron_energy = p + DELTA_NP_MEV if kind == "nue_n" else p - DELTA_NP_MEV
    momentum_sq = electron_energy**2 - M_E_MEV**2
    allowed = momentum_sq >= 0 if kind == "nue_n" else electron_energy >= M_E_MEV
    return np.where(
        allowed,
        electron_energy * np.sqrt(np.maximum(momentum_sq, 0.0)),
        0.0,
    )


def _capture_reference(m_mu: float, kind: str) -> float:
    # Fixed Gauss-Legendre integration is deterministic and avoids a SciPy dependency.
    nodes, weights = np.polynomial.legendre.leggauss(256)
    endpoint = m_mu / 2
    p = endpoint * (nodes + 1) / 2
    dp = endpoint / 2
    return float(np.sum(weights * dp * _michel_density(p, "nue", m_mu) * _capture_weight(p, kind)))


def _identity_errors(values: dict, expected: dict[str, str]) -> list[str]:
    errors = []
    exact_fields = {
        "blind_id": "blind_id",
        "source_payload_sha256": "source_payload_sha256",
        "source_card_version": "source_card_version",
        "source_payload_schema": "source_payload_schema",
        "source_package_version": "source_package_version",
        "source_card_json_sha256": "source_card_json_sha256",
        "source_payload_manifest_sha256": "payload_manifest_sha256",
        "source_payload_schema_document_sha256": "payload_schema_document_sha256",
    }
    float_fields = {
        "source_mass_MeV": "mass_MeV",
        "source_tau_s": "tau_s",
        "source_Y0": "Y0",
        "source_epsilon": "epsilon",
        "source_B_mumu": "B_mumu",
        "source_B_ee_plus_EMlike_neutral_effective": "B_ee_plus_EMlike_neutral_effective",
        "source_native_muon_multiplicity": "native_muon_multiplicity",
        "source_native_pion_multiplicity": "native_pion_multiplicity",
        "source_f_EM_integrated": "f_EM_integrated",
        "source_f_nu_integrated": "f_nu_integrated",
        "source_m_mu_MeV": "m_mu_MeV",
        "source_lifetime_factor": "lifetime_factor",
    }
    for actual_key, expected_key in exact_fields.items():
        expected_value = expected.get(expected_key)
        if is_placeholder(expected_value):
            errors.append(f"{actual_key}: frozen identity table field {expected_key} missing")
        elif norm(values.get(actual_key)) != norm(expected_value):
            errors.append(f"{actual_key}: frozen identity mismatch")
    for actual_key, expected_key in float_fields.items():
        expected_value = expected.get(expected_key)
        if is_placeholder(expected_value):
            errors.append(f"{actual_key}: frozen identity table field {expected_key} missing")
        elif not close_float(values.get(actual_key), expected_value):
            errors.append(f"{actual_key}: frozen identity mismatch")
    return errors


def validate_bridge(
    npz_path,
    metadata_path,
    expected_identity: dict[str, str] | None = None,
    *,
    allow_synthetic: bool = False,
):
    npz_path = Path(npz_path)
    metadata_path = Path(metadata_path)
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, object] = {}

    if not npz_path.is_file():
        return {"status": "FAIL", "errors": ["bridge NPZ missing"], "warnings": [], "metrics": {}, "metadata": {}}
    if not metadata_path.is_file():
        return {"status": "FAIL", "errors": ["bridge metadata JSON missing"], "warnings": [], "metrics": {}, "metadata": {}}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"metadata JSON parse failure: {exc}"], "warnings": [], "metrics": {}, "metadata": {}}

    if not isinstance(metadata, dict):
        return {"status": "FAIL", "errors": ["metadata JSON root must be an object"], "warnings": [], "metrics": {}, "metadata": {}}

    for key in META_REQUIRED:
        if is_placeholder(metadata.get(key)):
            errors.append(f"metadata {key}: blank or placeholder")
    if metadata.get("schema_version") != BRIDGE_SCHEMA:
        errors.append("metadata schema_version mismatch")
    if metadata.get("run_role") not in {"coarse", "fine"}:
        errors.append("metadata run_role must be coarse or fine")
    if metadata.get("momentum_coordinate_kind") not in {"comoving", "physical"}:
        errors.append("metadata momentum_coordinate_kind must be comoving or physical")
    if metadata.get("source_rhs_stage") != "pre_collision_pre_oscillation":
        errors.append("metadata source_rhs_stage must be pre_collision_pre_oscillation")
    if metadata.get("source_rhs_units") != "dY_per_dt_dq_s^-1":
        errors.append("metadata source_rhs_units must be dY_per_dt_dq_s^-1")
    if metadata.get("source_stepper_witness_method") != "paired_source_on_off":
        errors.append("metadata source_stepper_witness_method must be paired_source_on_off")
    if metadata.get("source_stepper_response_definition") != "on_minus_off_divided_by_step":
        errors.append("metadata source_stepper_response_definition must be on_minus_off_divided_by_step")
    if metadata.get("source_stepper_target_policy") != "nearest_t_over_tau":
        errors.append("metadata source_stepper_target_policy must be nearest_t_over_tau")
    if metadata.get("source_stepper_state_units") != "dY_dq":
        errors.append("metadata source_stepper_state_units must be dY_dq")
    if metadata.get("source_stepper_initial_state_definition") != "selected_bridge_state_dYdq":
        errors.append("metadata source_stepper_initial_state_definition must be selected_bridge_state_dYdq")
    if metadata.get("n_to_p_process_labels") != CANONICAL_N_TO_P_LABELS:
        errors.append("metadata n_to_p_process_labels must use the canonical v0.9.20 column order")
    if metadata.get("p_to_n_process_labels") != CANONICAL_P_TO_N_LABELS:
        errors.append("metadata p_to_n_process_labels must use the canonical v0.9.20 column order")
    if not valid_utc(metadata.get("generated_utc")):
        errors.append("metadata generated_utc must be ISO-8601 UTC")
    if norm(metadata.get("bridge_history_sha256")).lower() != sha256_file(npz_path):
        errors.append("metadata bridge_history_sha256 mismatch")
    if not allow_synthetic:
        if metadata.get("production_or_synthetic") != "production":
            errors.append("bridge metadata is not marked production")
        for key in (
            "backend_family", "backend_name", "backend_version_or_commit",
            "backend_environment", "state_export_method",
            "transport_stepper_production_callable",
            "transport_stepper_source_toggle", "operator_probe_command",
            "weak_rate_production_callable", "bbn_consumption_canary_command",
        ):
            if contains_marker(metadata.get(key)):
                errors.append(f"metadata {key}: non-production marker")

    preflight_errors, preflight_metrics = _npz_preflight(npz_path)
    errors.extend(preflight_errors)
    metrics.update(preflight_metrics)
    if preflight_errors:
        return {"schema": BRIDGE_SCHEMA, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics, "metadata": metadata}

    try:
        data = np.load(npz_path, allow_pickle=False)
    except Exception as exc:
        return {"status": "FAIL", "errors": errors + [f"NPZ load failure: {exc}"], "warnings": warnings, "metrics": metrics, "metadata": metadata}
    required = (
        REQ_SCALAR_TEXT + REQ_SCALAR_FLOAT + REQ_1D
        + REQ_2D + REQ_SOURCE_2D + REQ_STATE_2D
        + REQ_STEPPER_1D + REQ_STEPPER_2D + REQ_PROCESS_2D
    )
    for key in required:
        if key not in data.files:
            errors.append(f"missing array: {key}")
    if errors:
        data.close()
        return {"schema": BRIDGE_SCHEMA, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics, "metadata": metadata}

    values: dict[str, object] = {}
    try:
        for key in REQ_SCALAR_TEXT:
            values[key] = norm(_scalar(data[key]))
        for key in REQ_SCALAR_FLOAT:
            values[key] = float(_scalar(data[key]))
    except Exception as exc:
        data.close()
        errors.append(f"scalar parse failure: {exc}")
        return {"schema": BRIDGE_SCHEMA, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics, "metadata": metadata}
    if values["schema_version"] != BRIDGE_SCHEMA:
        errors.append("NPZ schema_version mismatch")
    source_hash_fields = (
        "source_payload_sha256", "source_card_json_sha256",
        "source_payload_manifest_sha256", "source_payload_schema_document_sha256",
    )
    for key in source_hash_fields:
        if not valid_sha256(values[key]):
            errors.append(f"{key} is not lowercase SHA-256")
    metadata_identity_fields = (
        "blind_id", "source_payload_sha256", "source_card_version",
        "source_payload_schema", "source_package_version",
        "source_card_json_sha256", "source_payload_manifest_sha256",
        "source_payload_schema_document_sha256",
    )
    for key in metadata_identity_fields:
        if norm(metadata.get(key)) != norm(values[key]):
            errors.append(f"metadata/NPZ {key} mismatch")
    for key in ("source_epsilon", "source_B_ee_plus_EMlike_neutral_effective"):
        try:
            if not close_float(metadata.get(key), values[key]):
                errors.append(f"metadata/NPZ {key} mismatch")
        except (TypeError, ValueError):
            errors.append(f"metadata {key} invalid")
    if values["source_card_version"] != CARD_SCHEMA:
        errors.append("source_card_version mismatch")
    if values["source_payload_schema"] != PAYLOAD_SCHEMA:
        errors.append("source_payload_schema mismatch")
    if values["source_package_version"] != PACKAGE:
        errors.append("source_package_version mismatch")
    if expected_identity is not None:
        errors.extend(_identity_errors(values, expected_identity))

    tau = float(values["source_tau_s"])
    m_mu = float(values["source_m_mu_MeV"])
    mass = float(values["source_mass_MeV"])
    yield0 = float(values["source_Y0"])
    epsilon = float(values["source_epsilon"])
    branch = float(values["source_B_mumu"])
    emlike_branch = float(values["source_B_ee_plus_EMlike_neutral_effective"])
    native_muons = float(values["source_native_muon_multiplicity"])
    native_pions = float(values["source_native_pion_multiplicity"])
    f_em = float(values["source_f_EM_integrated"])
    f_nu = float(values["source_f_nu_integrated"])
    lifetime_factor = float(values["source_lifetime_factor"])
    neutron_lifetime = float(values["neutron_lifetime_s"])
    yp = float(values["Yp_model"])
    dh = float(values["DH_x1e5_model"])
    neff = float(values["Neff_CMB_model"])
    if not all(math.isfinite(x) for x in (tau, m_mu, mass, yield0, epsilon, branch, emlike_branch, native_muons, native_pions, f_em, f_nu, lifetime_factor, neutron_lifetime, yp, dh, neff)):
        errors.append("non-finite scalar")
    if not (tau > 0 and 100 < m_mu < 110 and mass > 2 * m_mu and yield0 > 0 and epsilon > 0 and 0 <= branch <= 1 and 0 <= emlike_branch <= 1):
        errors.append("source scalar broad-range failure")
    if not close_float(branch + emlike_branch, 1.0, rtol=0, atol=2e-14):
        errors.append("source effective branching fractions do not sum to one")
    if not close_float(native_muons, 2 * branch) or native_pions != 0:
        errors.append("native multiplicity mapping mismatch")
    if not close_float(f_em + f_nu, 1.0, rtol=0, atol=2e-14):
        errors.append("source energy fractions do not sum to one")
    if not close_float(lifetime_factor, 18.0):
        errors.append("source lifetime factor is not frozen at 18")
    if not (800 < neutron_lifetime < 1000):
        errors.append("neutron_lifetime_s broad-range failure")
    if not (0 < yp < 1 and 0.01 < dh < 20 and 0 < neff < 20):
        errors.append("final outputs outside broad physical ranges")
    if "neutron_lifetime_s" in metadata:
        try:
            if not close_float(metadata["neutron_lifetime_s"], neutron_lifetime, rtol=2e-13):
                errors.append("metadata/NPZ neutron_lifetime_s mismatch")
        except Exception:
            errors.append("metadata neutron_lifetime_s invalid")

    try:
        arrays = {
            key: np.asarray(data[key], dtype=float)
            for key in (
                REQ_1D + REQ_2D + REQ_SOURCE_2D + REQ_STATE_2D
                + REQ_STEPPER_1D + REQ_STEPPER_2D + REQ_PROCESS_2D
            )
        }
    except Exception as exc:
        data.close()
        errors.append(f"array parse failure: {exc}")
        return {"schema": BRIDGE_SCHEMA, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics, "metadata": metadata, "identity": values}
    data.close()
    t = arrays["t_s"]
    a = arrays["scale_factor"]
    temperature = arrays["T_gamma_MeV"]
    q = arrays["q_grid"]
    q_weights = arrays["q_weights"]
    p_per_q = arrays["p_per_q_MeV"]
    rate_np = arrays["lambda_n_to_p_s_inv"]
    rate_pn = arrays["lambda_p_to_n_s_inv"]
    hubble = arrays["H_s_inv"]
    state_normalization = arrays["state_normalization_density_MeV3"]
    nt, nq = len(t), len(q)
    metrics.update({"time_points": nt, "momentum_bins": nq})
    if nt < 40:
        errors.append("time grid has fewer than 40 points")
    if nq < 21:
        errors.append("momentum grid has fewer than 21 points")
    if nt > 200000 or nq > 200000:
        errors.append("array dimension exceeds safety ceiling")
    for key in REQ_1D:
        array = arrays[key]
        expected_length = nq if key in {"q_grid", "q_weights"} else nt
        if array.ndim != 1 or len(array) != expected_length:
            errors.append(f"{key}: wrong shape")
        elif not np.all(np.isfinite(array)):
            errors.append(f"{key}: non-finite values")
    if not _strict_increasing(t) or abs(float(t[0])) > 1e-9:
        errors.append("t_s must start at zero and be strictly increasing")
    if np.any(a <= 0) or not _strict_increasing(a):
        errors.append("scale_factor must be positive and strictly increasing")
    if not _strict_increasing(q):
        errors.append("q_grid must be strictly increasing")
    if np.any(q <= 0) or np.any(q_weights <= 0):
        errors.append("q_grid and q_weights must be positive")
    if (
        np.any(temperature <= 0) or np.any(p_per_q <= 0)
        or np.any(hubble <= 0) or np.any(state_normalization <= 0)
    ):
        errors.append("temperature, momentum scale, Hubble history, and state normalization must be positive")
    if np.any(rate_np <= 0) or np.any(rate_pn < 0):
        errors.append("weak-rate histories must be nonnegative and n-to-p strictly positive")
    if not _mostly_decreasing(temperature):
        errors.append("T_gamma_MeV is not predominantly decreasing")
    injection_cutoff = tau * lifetime_factor
    if t[-1] < max(THRESHOLDS["t_end_min_s"], injection_cutoff):
        errors.append("history ends before BBN/source injection coverage is complete")
    if temperature[0] < THRESHOLDS["T_start_min_MeV"]:
        errors.append("history starts below 3 MeV")
    if temperature[-1] > THRESHOLDS["T_end_max_MeV"]:
        errors.append("history ends above 0.05 MeV")

    for key in REQ_2D:
        array = arrays[key]
        if array.shape != (nt, nq):
            errors.append(f"{key}: expected shape {(nt, nq)}, got {array.shape}")
        elif not np.all(np.isfinite(array)):
            errors.append(f"{key}: non-finite values")
        elif np.min(array) < -THRESHOLDS["occupancy_tolerance"] or np.max(array) > 1 + THRESHOLDS["occupancy_tolerance"]:
            errors.append(f"{key}: occupation outside [0,1]")
    for key in REQ_SOURCE_2D:
        array = arrays[key]
        if array.shape != (nt, nq):
            errors.append(f"{key}: expected shape {(nt, nq)}, got {array.shape}")
        elif not np.all(np.isfinite(array)) or np.any(array < 0):
            errors.append(f"{key}: source RHS must be finite and nonnegative")
    for key in REQ_STATE_2D:
        array = arrays[key]
        if array.shape != (nt, nq):
            errors.append(f"{key}: expected shape {(nt, nq)}, got {array.shape}")
        elif not np.all(np.isfinite(array)) or np.any(array < 0):
            errors.append(f"{key}: canonical state must be finite and nonnegative")
    witness_rows = len(STEPPER_TARGET_T_OVER_TAU)
    for key in REQ_STEPPER_1D:
        array = arrays[key]
        if array.shape != (witness_rows,):
            errors.append(f"{key}: expected shape {(witness_rows,)}, got {array.shape}")
        elif not np.all(np.isfinite(array)):
            errors.append(f"{key}: non-finite values")
    for key in REQ_STEPPER_2D:
        array = arrays[key]
        if array.shape != (witness_rows, nq):
            errors.append(f"{key}: expected shape {(witness_rows, nq)}, got {array.shape}")
        elif not np.all(np.isfinite(array)) or np.any(array < 0):
            errors.append(f"{key}: witness state must be finite and nonnegative")
    for key, total, labels_key, expected_columns in (
        ("lambda_n_to_p_process_s_inv", rate_np, "n_to_p_process_labels", 3),
        ("lambda_p_to_n_process_s_inv", rate_pn, "p_to_n_process_labels", 2),
    ):
        array = arrays[key]
        if array.ndim != 2 or array.shape != (nt, expected_columns):
            errors.append(f"{key}: expected canonical shape {(nt, expected_columns)}")
            continue
        if not np.all(np.isfinite(array)) or np.any(array < 0):
            errors.append(f"{key}: process rates must be finite and nonnegative")
            continue
        labels = metadata.get(labels_key)
        if not isinstance(labels, list) or len(labels) != array.shape[1] or len(set(map(str, labels))) != len(labels) or any(is_placeholder(label) for label in labels):
            errors.append(f"metadata {labels_key} must uniquely label every process column")
            continue
        residual = np.abs(total - np.sum(array, axis=1))
        ceiling = 1e-14 + 1e-10 * np.abs(total)
        metrics[f"{key}_sum_max_abs_residual"] = float(np.max(residual))
        metrics[f"{key}_sum_max_scaled_residual"] = float(np.max(residual / np.maximum(ceiling, 1e-300)))
        if np.any(residual > ceiling):
            errors.append(f"{key}: process sum does not close to exported total")
    if errors:
        # Avoid expensive quadrature on malformed arrays.
        return {"schema": BRIDGE_SCHEMA, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics, "metadata": metadata, "identity": values}

    # The exported expansion history must be globally consistent with da/a=Hdt.
    scale_factor_log_growth = float(math.log(a[-1]) - math.log(a[0]))
    integrated_hubble_dt = float(np.trapezoid(hubble, t))
    expansion_residual = integrated_hubble_dt - scale_factor_log_growth
    expansion_scale = max(abs(integrated_hubble_dt), abs(scale_factor_log_growth), 1e-12)
    expansion_scaled_relerr = abs(expansion_residual) / expansion_scale
    if not all(math.isfinite(value) for value in (scale_factor_log_growth, integrated_hubble_dt, expansion_residual, expansion_scaled_relerr)):
        expansion_scaled_relerr = math.inf
    metrics.update({
        "scale_factor_log_growth": scale_factor_log_growth,
        "integrated_H_dt": integrated_hubble_dt,
        "hubble_scale_factor_integral_abs_residual": abs(expansion_residual),
        "hubble_scale_factor_integral_scaled_relerr": expansion_scaled_relerr,
    })
    if expansion_scaled_relerr > THRESHOLDS["hubble_scale_factor_integral_relerr_max"]:
        errors.append("Hubble/scale-factor global integral-closure gate failed")

    coordinate_kind = metadata.get("momentum_coordinate_kind")
    conversion_invariant = a * p_per_q if coordinate_kind == "comoving" else p_per_q
    conversion_rel_spread = float(np.max(np.abs(conversion_invariant / conversion_invariant[0] - 1)))
    metrics["momentum_conversion_invariant_max_abs_relerr"] = conversion_rel_spread
    if conversion_rel_spread > 5e-3:
        errors.append(f"{coordinate_kind} momentum-coordinate conversion is inconsistent with scale-factor history")

    # Frozen source-history closure uses the exact half-open convention
    # [0,18*tau).  A sample exactly at the cutoff is source-off and is tested,
    # rather than being discarded as a measure-zero ambiguity.
    active, after, injection_cutoff = _half_open_source_masks(t, tau, lifetime_factor)
    decay = yield0 * np.exp(-t / tau) / tau
    source_expected = np.where(active, decay, 0.0)
    muon_pair_expected = branch * source_expected
    qem_expected = f_em * mass * source_expected
    qnu_expected = f_nu * mass * source_expected
    history_pairs = [
        ("source_dYdt", arrays["source_dYdt_s_inv"], source_expected),
        ("source_muon_pair_dYdt", arrays["source_muon_pair_dYdt_s_inv"], muon_pair_expected),
        ("source_Q_EM", arrays["source_Q_EM_over_s_MeV_s_inv"], qem_expected),
        ("source_Q_nu", arrays["source_Q_nu_over_s_MeV_s_inv"], qnu_expected),
    ]
    for label, actual, expected_values in history_pairs:
        scale = max(float(np.max(np.abs(expected_values))), 1e-300)
        relerr = float(np.max(np.abs(actual - expected_values)) / scale)
        metrics[f"{label}_formula_relerr"] = relerr
        if relerr > THRESHOLDS["source_history_relerr_max"]:
            errors.append(f"{label} frozen formula gate failed")
    qpi_max = float(np.max(np.abs(arrays["source_Q_pi_charged_over_s_MeV_s_inv"])))
    metrics["source_Q_pi_max_abs"] = qpi_max
    if qpi_max != 0:
        errors.append("charged-pion source is nonzero")
    numeric_source = float(np.trapezoid(arrays["source_dYdt_s_inv"], t))
    analytic_source = yield0 * (1 - math.exp(-lifetime_factor))
    source_integral_relerr = numeric_source / analytic_source - 1
    metrics["source_integral_relerr"] = source_integral_relerr
    if abs(source_integral_relerr) > THRESHOLDS["source_integral_relerr_max"]:
        errors.append("integrated source-history gate failed")

    # Actual production source-operator closure.  These arrays are the
    # canonical dY/(dt dq) injection RHS exported before collisions and flavor
    # evolution; unlike the representability checks below, they test what the
    # backend says it really inserted into the transport equations.
    source_keys = {
        "nue": "source_rhs_nue_dYdt_dq_s_inv",
        "nuebar": "source_rhs_nuebar_dYdt_dq_s_inv",
        "numu": "source_rhs_numu_dYdt_dq_s_inv",
        "numubar": "source_rhs_numubar_dYdt_dq_s_inv",
        "nutau": "source_rhs_nutau_dYdt_dq_s_inv",
        "nutaubar": "source_rhs_nutaubar_dYdt_dq_s_inv",
    }
    expected_source_arrays = {
        species: _expected_source_rhs(
            q, p_per_q, source_expected, branch, m_mu, species,
        )
        for species in STATE_SPECIES
    }
    expected_active_peak = max(
        float(np.max(expected_source_arrays[species][active]))
        for species in SOURCE_ACTIVE_SPECIES
    )
    zero_ceiling = max(
        expected_active_peak * THRESHOLDS["source_rhs_zero_peak_rel_ceiling"],
        1e-300,
    )
    metrics["source_rhs_expected_active_peak"] = expected_active_peak
    metrics["source_rhs_zero_absolute_ceiling"] = zero_ceiling

    # Direct shape comparison on the returned nodes.  The 5e-4 L1/CDF limits
    # are intentionally tighter than the continuum-moment gate because the
    # expected and actual arrays use the identical discrete measure.
    endpoint = m_mu / 2
    shape_gate_failures: dict[str, set[str]] = {
        species: set() for species in SOURCE_ACTIVE_SPECIES
    }
    for species in SOURCE_ACTIVE_SPECIES:
        l1_values = []
        cdf_values = []
        peak_values = []
        support_values = []
        actual_source = arrays[source_keys[species]]
        expected_source = expected_source_arrays[species]
        for row in np.flatnonzero(active):
            l1, cdf_sup, peak_scaled = _weighted_shape_metrics(
                actual_source[row], expected_source[row], q_weights,
            )
            l1_values.append(l1)
            cdf_values.append(cdf_sup)
            peak_values.append(peak_scaled)
            row_peak = max(float(np.max(expected_source[row])), 1e-300)
            above_endpoint = q * p_per_q[row] > endpoint
            support_scaled = (
                float(np.max(np.abs(actual_source[row][above_endpoint]))) / row_peak
                if np.any(above_endpoint) else 0.0
            )
            support_values.append(support_scaled)
        maxima = {
            "weighted_l1": float(max(l1_values, default=math.inf)),
            "cdf_sup": float(max(cdf_values, default=math.inf)),
            "peak_scaled": float(max(peak_values, default=math.inf)),
            "above_endpoint_peak_scaled": float(max(support_values, default=math.inf)),
        }
        for label, value in maxima.items():
            metrics[f"source_rhs_{species}_shape_{label}_max"] = value
        if maxima["weighted_l1"] > THRESHOLDS["source_rhs_shape_weighted_l1_max"]:
            shape_gate_failures[species].add("weighted-L1")
        if maxima["cdf_sup"] > THRESHOLDS["source_rhs_shape_cdf_sup_max"]:
            shape_gate_failures[species].add("CDF")
        if maxima["peak_scaled"] > THRESHOLDS["source_rhs_shape_peak_scaled_max"]:
            shape_gate_failures[species].add("peak")
        if maxima["above_endpoint_peak_scaled"] > THRESHOLDS["source_rhs_zero_peak_rel_ceiling"]:
            shape_gate_failures[species].add("endpoint-support")
    for species, failures in shape_gate_failures.items():
        if failures:
            errors.append(
                f"actual source RHS {species} direct-shape gate failed: "
                + ",".join(sorted(failures))
            )

    # Neutrino/antineutrino equality and the tau-zero condition are scaled at
    # every active row.  A global peak cannot hide a late-time flavor defect.
    for left, right, metric_label in (
        ("nue", "nuebar", "electron"),
        ("numu", "numubar", "muon"),
    ):
        a_source = arrays[source_keys[left]]
        b_source = arrays[source_keys[right]]
        pair_row_errors = []
        for row in np.flatnonzero(active):
            row_scale = max(
                float(np.max(expected_source_arrays[left][row])),
                float(np.max(expected_source_arrays[right][row])),
                1e-300,
            )
            pair_row_errors.append(float(np.max(np.abs(a_source[row] - b_source[row]))) / row_scale)
        pair_relerr = float(max(pair_row_errors, default=math.inf))
        metrics[f"source_rhs_{metric_label}_nu_antinu_max_relerr"] = pair_relerr
        if pair_relerr > THRESHOLDS["source_rhs_flavor_pair_relerr_max"]:
            errors.append(f"source RHS {metric_label}-flavor neutrino/antineutrino equality gate failed")
    tau_row_scaled = []
    for row in np.flatnonzero(active):
        row_scale = max(
            float(np.max(expected_source_arrays[species][row]))
            for species in SOURCE_ACTIVE_SPECIES
        )
        tau_row_scaled.append(max(
            float(np.max(np.abs(arrays[source_keys[label]][row]))) / max(row_scale, 1e-300)
            for label in ("nutau", "nutaubar")
        ))
    tau_scaled_max = float(max(tau_row_scaled, default=math.inf))
    tau_max = max(float(np.max(np.abs(arrays[source_keys[label]]))) for label in ("nutau", "nutaubar"))
    metrics["source_rhs_tau_max_abs"] = tau_max
    metrics["source_rhs_tau_rowwise_peak_scaled_max"] = tau_scaled_max
    if tau_scaled_max > THRESHOLDS["source_rhs_zero_peak_rel_ceiling"]:
        errors.append("source RHS tau-flavor zero gate failed")
    after_max = max(
        float(np.max(np.abs(arrays[source_keys[label]][after]))) if np.any(after) else 0.0
        for label in source_keys
    )
    metrics["source_rhs_after_cutoff_max_abs"] = after_max
    if after_max > zero_ceiling:
        errors.append("source RHS remains nonzero after the frozen injection cutoff")

    source_moment_errors = []
    moment_arrays = {
        "nue": arrays[source_keys["nue"]],
        "numu": arrays[source_keys["numu"]],
    }
    for label, source_array in moment_arrays.items():
        for k in range(6):
            basis = q_weights * q**k
            numeric = p_per_q**k * np.dot(source_array, basis)
            exact = branch * source_expected * endpoint**k * _michel_moment_x(label, k)
            relerrs = numeric[active] / exact[active] - 1
            max_abs_relerr = float(np.max(np.abs(relerrs)))
            metrics[f"source_rhs_{label}_E{k}_max_abs_relerr"] = max_abs_relerr
            source_moment_errors.append(max_abs_relerr)
            if max_abs_relerr > THRESHOLDS["source_rhs_Ek_abs_relerr_max"]:
                errors.append(f"actual source RHS {label} E^{k} closure gate failed")
    metrics["source_rhs_Ek_global_max_abs_relerr"] = float(max(source_moment_errors))

    active_source_sum = sum(
        arrays[source_keys[label]]
        for label in ("nue", "nuebar", "numu", "numubar")
    )
    total_number = np.dot(active_source_sum, q_weights)
    total_energy = p_per_q * np.dot(active_source_sum, q_weights * q)
    expected_number = 4 * branch * source_expected
    expected_energy = f_nu * mass * source_expected
    total_number_relerr = float(np.max(np.abs(total_number[active] / expected_number[active] - 1)))
    total_energy_relerr = float(np.max(np.abs(total_energy[active] / expected_energy[active] - 1)))
    metrics["source_rhs_total_number_max_abs_relerr"] = total_number_relerr
    metrics["source_rhs_total_energy_max_abs_relerr"] = total_energy_relerr
    if max(total_number_relerr, total_energy_relerr) > THRESHOLDS["source_rhs_Ek_abs_relerr_max"]:
        errors.append("actual source RHS total number/energy closure gate failed")

    integrated_total_number = float(np.trapezoid(total_number, t))
    integrated_total_energy = float(np.trapezoid(total_energy, t))
    analytic_total_number = 4 * branch * analytic_source
    analytic_total_energy = f_nu * mass * analytic_source
    integrated_number_relerr = integrated_total_number / analytic_total_number - 1
    integrated_energy_relerr = integrated_total_energy / analytic_total_energy - 1
    metrics.update({
        "source_rhs_time_integrated_total_number": integrated_total_number,
        "source_rhs_time_integrated_total_energy_MeV": integrated_total_energy,
        "source_rhs_time_integrated_number_relerr": integrated_number_relerr,
        "source_rhs_time_integrated_energy_relerr": integrated_energy_relerr,
    })
    if max(abs(integrated_number_relerr), abs(integrated_energy_relerr)) > THRESHOLDS["source_rhs_time_integral_relerr_max"]:
        errors.append("actual source RHS time-integrated number/energy closure gate failed")

    # Endpoint-domain gate, evaluated at the frozen injection cutoff.
    pscale_cutoff = float(np.interp(injection_cutoff, t, p_per_q))
    pmax_cutoff = float(q[-1] * pscale_cutoff)
    endpoint = m_mu / 2
    active_pscales = list(np.asarray(p_per_q[t <= injection_cutoff], dtype=float))
    active_pscales.append(pscale_cutoff)
    pmax_min = float(q[-1] * min(active_pscales))
    endpoint_margin = pmax_min / endpoint - 1
    metrics.update({
        "injection_cutoff_s": injection_cutoff,
        "pmax_at_injection_cutoff_MeV": pmax_cutoff,
        "minimum_pmax_during_injection_MeV": pmax_min,
        "muon_endpoint_MeV": endpoint,
        "endpoint_relative_margin": endpoint_margin,
    })
    if endpoint_margin < THRESHOLDS["endpoint_rel_margin_min"]:
        errors.append("momentum domain clips the stopped-muon endpoint before injection cutoff")

    # Thermal M3 must be accurate throughout the exported history, not merely
    # at one time point where a normalization cancellation may hide error.
    thermal_errors = []
    for pscale, temp in zip(p_per_q, temperature):
        u = q * pscale / temp
        du = q_weights * pscale / temp
        with np.errstate(over="ignore"):
            ffd = np.where(u < 700, 1 / (np.exp(u) + 1), 0.0)
        thermal_errors.append(float(np.sum(du * u**3 * ffd) / M3_EXACT - 1))
    thermal_max = float(np.max(np.abs(thermal_errors)))
    metrics["thermal_M3_max_abs_relerr"] = thermal_max
    metrics["thermal_M3_first_relerr"] = thermal_errors[0]
    if thermal_max > THRESHOLDS["thermal_M3_abs_relerr_max"]:
        errors.append("thermal M3 quadrature gate failed")

    # The actual six initial distribution arrays must carry the expected
    # relativistic third moment, independently of the ideal FD grid audit.
    u_initial = q * p_per_q[0] / temperature[0]
    du_initial = q_weights * p_per_q[0] / temperature[0]
    with np.errstate(over="ignore"):
        fd_initial = np.where(u_initial < 700, 1 / (np.exp(u_initial) + 1), 0.0)
    fd_number_measure = q_weights * q**2
    initial_distribution_m3_relerrs = []
    initial_fd_l1_values = []
    initial_fd_cdf_values = []
    physical_e3_basis = q_weights * q**3
    for key in REQ_2D:
        distribution = arrays[key]
        fd_l1, fd_cdf_sup, _ = _weighted_shape_metrics(
            distribution[0], fd_initial, fd_number_measure,
        )
        metrics[f"{key}_initial_FD_weighted_l1"] = fd_l1
        metrics[f"{key}_initial_FD_cdf_sup"] = fd_cdf_sup
        initial_fd_l1_values.append(fd_l1)
        initial_fd_cdf_values.append(fd_cdf_sup)
        if fd_l1 > THRESHOLDS["initial_fd_weighted_l1_max"]:
            errors.append(f"{key}: initial FD weighted-L1 gate failed")
        if fd_cdf_sup > THRESHOLDS["initial_fd_cdf_sup_max"]:
            errors.append(f"{key}: initial FD normalized-CDF gate failed")
        initial_m3 = float(np.sum(du_initial * u_initial**3 * distribution[0]))
        initial_relerr = initial_m3 / M3_EXACT - 1
        metrics[f"{key}_initial_M3_relerr"] = initial_relerr
        initial_distribution_m3_relerrs.append(abs(initial_relerr))

        physical_e3_history = p_per_q**4 * np.dot(distribution, physical_e3_basis)
        metrics[f"{key}_physical_E3_moment_min_MeV4"] = float(np.min(physical_e3_history))
        metrics[f"{key}_physical_E3_moment_max_MeV4"] = float(np.max(physical_e3_history))
        if not np.all(np.isfinite(physical_e3_history)) or np.any(physical_e3_history <= 0):
            errors.append(f"{key}: physical E^3 moment is nonpositive or non-finite over history")
    initial_distribution_m3_max = float(max(initial_distribution_m3_relerrs))
    metrics["initial_distribution_M3_max_abs_relerr"] = initial_distribution_m3_max
    metrics["initial_FD_weighted_l1_max"] = float(max(initial_fd_l1_values))
    metrics["initial_FD_cdf_sup_max"] = float(max(initial_fd_cdf_values))
    if initial_distribution_m3_max > THRESHOLDS["initial_distribution_M3_abs_relerr_max"]:
        errors.append("initial six-distribution M3 gate failed")

    # Canonical transport state.  This closes the ambiguity between an
    # occupation-number export and the yield-density state advanced by the
    # production stepper:
    #   dY/dq = f(q) q^2 p_per_q^3 / (2*pi^2*s).
    state_mapping_l1 = []
    state_mapping_peak = []
    for species, distribution_key in zip(STATE_SPECIES, REQ_2D):
        actual_state = arrays[f"state_dYdq_{species}"]
        expected_state = _state_dydq_from_f(
            arrays[distribution_key], q, p_per_q, state_normalization,
        )
        species_l1 = []
        species_peak = []
        for row in range(nt):
            l1, _, peak_scaled = _weighted_shape_metrics(
                actual_state[row], expected_state[row], q_weights,
            )
            species_l1.append(l1)
            species_peak.append(peak_scaled)
        max_l1 = float(max(species_l1, default=math.inf))
        max_peak = float(max(species_peak, default=math.inf))
        metrics[f"state_dYdq_{species}_mapping_weighted_l1_max"] = max_l1
        metrics[f"state_dYdq_{species}_mapping_peak_scaled_max"] = max_peak
        state_mapping_l1.append(max_l1)
        state_mapping_peak.append(max_peak)
        if max_l1 > THRESHOLDS["state_mapping_weighted_l1_max"]:
            errors.append(f"state_dYdq_{species}: f-to-state weighted-L1 mapping gate failed")
        if max_peak > THRESHOLDS["state_mapping_peak_scaled_max"]:
            errors.append(f"state_dYdq_{species}: f-to-state peak mapping gate failed")
    metrics["state_dYdq_mapping_weighted_l1_global_max"] = float(max(state_mapping_l1))
    metrics["state_dYdq_mapping_peak_scaled_global_max"] = float(max(state_mapping_peak))

    # Deterministic source-on/off production-stepper witness.  At eight fixed
    # t/tau targets the nearest bridge row is selected with a first-index tie
    # break.  The validator derives the response from paired on/off states,
    # rather than accepting a backend-reported derivative at face value.
    witness_targets = arrays["source_stepper_target_t_over_tau"]
    witness_index_raw = arrays["source_stepper_time_index"]
    witness_sample_t = arrays["source_stepper_sample_t_s"]
    witness_h = arrays["source_stepper_h_s"]
    witness_h2 = arrays["source_stepper_h2_s"]
    nearest_indices = _nearest_target_indices(t, tau)
    witness_structure_valid = True
    if not np.allclose(witness_targets, STEPPER_TARGET_T_OVER_TAU, rtol=0, atol=1e-15):
        errors.append("source stepper target t/tau vector mismatch")
        witness_structure_valid = False
    rounded_index_values = np.rint(witness_index_raw)
    if not np.allclose(witness_index_raw, rounded_index_values, rtol=0, atol=1e-12):
        errors.append("source stepper time indices are not integer-valued")
        witness_structure_valid = False
    if np.any(rounded_index_values < 0) or np.any(rounded_index_values >= nt):
        errors.append("source stepper time index outside bridge history")
        witness_structure_valid = False
        rounded_indices = np.zeros_like(nearest_indices)
    else:
        rounded_indices = rounded_index_values.astype(int)
    if witness_structure_valid and not np.array_equal(rounded_indices, nearest_indices):
        errors.append("source stepper rows are not the deterministic nearest t/tau targets")
        witness_structure_valid = False
    if witness_structure_valid and (
        len(set(map(int, rounded_indices))) != len(rounded_indices)
        or np.any(np.diff(rounded_indices) <= 0)
    ):
        errors.append("source stepper nearest rows must be unique and strictly increasing")
        witness_structure_valid = False
    if witness_structure_valid and not np.allclose(
        witness_sample_t, t[rounded_indices], rtol=2e-13, atol=1e-14,
    ):
        errors.append("source stepper sample times do not match selected bridge rows")
        witness_structure_valid = False
    if np.any(witness_h <= 0) or np.any(witness_h2 <= 0):
        errors.append("source stepper h and h/2 must be positive")
        witness_structure_valid = False
    if not np.allclose(witness_h2, witness_h / 2, rtol=2e-13, atol=1e-15):
        errors.append("source stepper h/2 vector is not exactly the declared refinement")
        witness_structure_valid = False
    if witness_structure_valid:
        if np.any(~active[rounded_indices]):
            errors.append("source stepper witness includes a source-off target row")
            witness_structure_valid = False
        if np.any(witness_sample_t + witness_h > injection_cutoff):
            errors.append("source stepper h crosses the half-open source cutoff")
            witness_structure_valid = False

    metrics["source_stepper_nearest_time_ratio_max_abs_error"] = float(np.max(
        np.abs(t[nearest_indices] / tau - STEPPER_TARGET_T_OVER_TAU)
    ))
    if witness_structure_valid:
        for species in STATE_SPECIES:
            rhs = arrays[source_keys[species]]
            witness_initial = arrays[f"source_stepper_initial_state_dYdq_{species}"]
            selected_initial = arrays[f"state_dYdq_{species}"][rounded_indices]
            initial_l1_values = []
            initial_peak_values = []
            for witness_row in range(len(rounded_indices)):
                initial_l1, _, initial_peak = _weighted_shape_metrics(
                    witness_initial[witness_row], selected_initial[witness_row], q_weights,
                )
                initial_l1_values.append(initial_l1)
                initial_peak_values.append(initial_peak)
            initial_l1_max = float(max(initial_l1_values, default=math.inf))
            initial_peak_max = float(max(initial_peak_values, default=math.inf))
            metrics[f"source_stepper_{species}_initial_state_weighted_l1_max"] = initial_l1_max
            metrics[f"source_stepper_{species}_initial_state_peak_scaled_max"] = initial_peak_max
            if initial_l1_max > THRESHOLDS["state_mapping_weighted_l1_max"] or initial_peak_max > THRESHOLDS["state_mapping_peak_scaled_max"]:
                errors.append(f"source stepper {species} initial state is not bound to the selected bridge state")
            l1_h_values = []
            l1_h2_values = []
            l1_halving_values = []
            moment_h_errors = []
            moment_h2_errors = []
            moment_halving_errors = []
            zero_response_scaled = []
            on_h = arrays[f"source_stepper_on_h_state_dYdq_{species}"]
            off_h = arrays[f"source_stepper_off_h_state_dYdq_{species}"]
            on_h2 = arrays[f"source_stepper_on_h2_state_dYdq_{species}"]
            off_h2 = arrays[f"source_stepper_off_h2_state_dYdq_{species}"]
            response_h_all = _paired_stepper_response(on_h, off_h, witness_h)
            response_h2_all = _paired_stepper_response(on_h2, off_h2, witness_h2)
            for witness_row, history_row in enumerate(rounded_indices):
                response_h = response_h_all[witness_row]
                response_h2 = response_h2_all[witness_row]
                reference = rhs[history_row]
                if species in SOURCE_ACTIVE_SPECIES:
                    l1_h, _, _ = _weighted_shape_metrics(response_h, reference, q_weights)
                    l1_h2, _, _ = _weighted_shape_metrics(response_h2, reference, q_weights)
                    l1_halving, _, _ = _weighted_shape_metrics(response_h, response_h2, q_weights)
                    l1_h_values.append(l1_h)
                    l1_h2_values.append(l1_h2)
                    l1_halving_values.append(l1_halving)
                    for order in range(6):
                        reference_moment = _moment(reference, q, q_weights, p_per_q[history_row], order)
                        response_h_moment = _moment(response_h, q, q_weights, p_per_q[history_row], order)
                        response_h2_moment = _moment(response_h2, q, q_weights, p_per_q[history_row], order)
                        if reference_moment <= 0 or response_h2_moment <= 0:
                            h_error = h2_error = halving_error = math.inf
                        else:
                            h_error = abs(response_h_moment / reference_moment - 1)
                            h2_error = abs(response_h2_moment / reference_moment - 1)
                            halving_error = abs(response_h_moment / response_h2_moment - 1)
                        moment_h_errors.append(h_error)
                        moment_h2_errors.append(h2_error)
                        moment_halving_errors.append(halving_error)
                else:
                    row_scale = max(
                        float(np.max(expected_source_arrays[label][history_row]))
                        for label in SOURCE_ACTIVE_SPECIES
                    )
                    zero_response_scaled.append(max(
                        float(np.max(np.abs(response_h))),
                        float(np.max(np.abs(response_h2))),
                    ) / max(row_scale, 1e-300))
            if species in SOURCE_ACTIVE_SPECIES:
                maxima = {
                    "response_h_weighted_l1": float(max(l1_h_values, default=math.inf)),
                    "response_h2_weighted_l1": float(max(l1_h2_values, default=math.inf)),
                    "response_halving_weighted_l1": float(max(l1_halving_values, default=math.inf)),
                    "response_h_moment_relerr": float(max(moment_h_errors, default=math.inf)),
                    "response_h2_moment_relerr": float(max(moment_h2_errors, default=math.inf)),
                    "response_halving_moment_relerr": float(max(moment_halving_errors, default=math.inf)),
                }
                for label, value in maxima.items():
                    metrics[f"source_stepper_{species}_{label}_max"] = value
                if max(maxima["response_h_weighted_l1"], maxima["response_h2_weighted_l1"]) > THRESHOLDS["stepper_response_weighted_l1_max"]:
                    errors.append(f"source stepper {species} direct response weighted-L1 gate failed")
                if maxima["response_halving_weighted_l1"] > THRESHOLDS["stepper_halving_weighted_l1_max"]:
                    errors.append(f"source stepper {species} h/h2 weighted-L1 consistency gate failed")
                if max(maxima["response_h_moment_relerr"], maxima["response_h2_moment_relerr"]) > THRESHOLDS["stepper_response_moment_relerr_max"]:
                    errors.append(f"source stepper {species} k0..5 response gate failed")
                if maxima["response_halving_moment_relerr"] > THRESHOLDS["stepper_halving_moment_relerr_max"]:
                    errors.append(f"source stepper {species} h/h2 k0..5 consistency gate failed")
            else:
                zero_max = float(max(zero_response_scaled, default=math.inf))
                metrics[f"source_stepper_{species}_zero_response_peak_scaled_max"] = zero_max
                if zero_max > THRESHOLDS["source_rhs_zero_peak_rel_ceiling"]:
                    errors.append(f"source stepper {species} zero-response gate failed")

    # Decay-weighted Michel E^k moments through k=5.
    time_weights = _time_weights(t)
    decay_weight = np.where(active, np.exp(-t / tau) / tau, 0.0)
    normalization = float(np.sum(time_weights * decay_weight))
    if normalization <= 0:
        errors.append("invalid decay-weight time normalization")
    else:
        normalized_time_weight = time_weights * decay_weight / normalization
        moment_sums = {(label, k): 0.0 for label in ("nue", "numu") for k in range(6)}
        capture_sums = {kind: 0.0 for kind in ("nue_n", "nuebar_p")}
        for index in range(nt):
            if normalized_time_weight[index] == 0:
                continue
            p = q * p_per_q[index]
            dp = q_weights * p_per_q[index]
            for label in ("nue", "numu"):
                density = _michel_density(p, label, m_mu)
                for k in range(6):
                    moment_sums[(label, k)] += normalized_time_weight[index] * float(np.sum(dp * density * p**k))
            density_e = _michel_density(p, "nue", m_mu)
            for kind in capture_sums:
                capture_sums[kind] += normalized_time_weight[index] * float(np.sum(dp * density_e * _capture_weight(p, kind)))
        for label in ("nue", "numu"):
            for k in range(6):
                exact = (m_mu / 2) ** k * _michel_moment_x(label, k)
                relerr = moment_sums[(label, k)] / exact - 1
                metrics[f"{label}_E{k}_relerr"] = relerr
                if abs(relerr) > THRESHOLDS["michel_Ek_abs_relerr_max"]:
                    errors.append(f"{label} E^{k} Michel quadrature gate failed")
        for kind, numeric in capture_sums.items():
            exact = _capture_reference(m_mu, kind)
            relerr = numeric / exact - 1
            metrics[f"{kind}_capture_proxy_relerr"] = relerr
            if abs(relerr) > THRESHOLDS["capture_proxy_abs_relerr_max"]:
                errors.append(f"{kind} Born capture-proxy gate failed")

    # Broad physical sanity checks.  These do not replace backend review.
    early = temperature >= 3.0
    if np.any(early):
        hrad = 1.66 * math.sqrt(GSTAR_EARLY) * temperature[early]**2 / MPL_MEV / HBAR_MEV_S
        hratio = hubble[early] / hrad
        metrics["early_H_over_radiation_min"] = float(np.min(hratio))
        metrics["early_H_over_radiation_max"] = float(np.max(hratio))
        if np.min(hratio) < 0.25 or np.max(hratio) > 4.0:
            errors.append("early Hubble history fails broad radiation-era sanity")
        first = int(np.flatnonzero(early)[0])
        expected_ratio = math.exp(-DELTA_NP_MEV / temperature[first])
        actual_ratio = rate_pn[first] / rate_np[first]
        metrics["early_rate_detailed_balance_relerr"] = actual_ratio / expected_ratio - 1
        if abs(actual_ratio / expected_ratio - 1) > 0.5:
            errors.append("early weak-rate ratio fails broad detailed-balance sanity")
    late = temperature <= 0.05
    if np.any(late):
        late_np_tau = rate_np[late] * neutron_lifetime
        metrics["late_lambda_np_times_tau_n_median"] = float(np.median(late_np_tau))
        if np.median(late_np_tau) < 0.5 or np.median(late_np_tau) > 2.0:
            errors.append("late n-to-p rate is inconsistent with declared neutron lifetime")
        late_ratio = rate_pn[late] / rate_np[late]
        metrics["late_lambda_pn_over_np_max"] = float(np.max(late_ratio))
        if np.max(late_ratio) > 0.2:
            errors.append("late p-to-n rate is too large relative to n-to-p")

    metrics.update({
        "Yp_model": yp, "DH_x1e5_model": dh, "Neff_CMB_model": neff,
        "T_start_MeV": float(temperature[0]), "T_end_MeV": float(temperature[-1]),
        "t_start_s": float(t[0]), "t_end_s": float(t[-1]),
        "run_role": metadata.get("run_role"),
    })
    return {
        "schema": BRIDGE_SCHEMA,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "metadata": metadata,
        "identity": values,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bridge_npz")
    parser.add_argument("metadata_json")
    parser.add_argument("--base", default=".")
    parser.add_argument("--expected-blind-id", required=True)
    parser.add_argument("--out-json", default="DMDE_v0920_bridge_validation.json")
    args = parser.parse_args()
    expected_map = load_expected(Path(args.base))
    expected = expected_map.get(args.expected_blind_id)
    if expected is None:
        parser.error(f"unknown --expected-blind-id: {args.expected_blind_id}")
    result = validate_bridge(args.bridge_npz, args.metadata_json, expected, allow_synthetic=False)
    Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"BRIDGE VALIDATION {result['status']}: {args.bridge_npz}")
    if result["status"] != "PASS":
        for error in result["errors"]:
            print("ERROR:", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
