#!/usr/bin/env python3
"""Strict two-card DMDE v0.9.20 provider-return firewall."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from dmde_v0920_common import (
    BRIDGE_SCHEMA, CARD_SCHEMA, INVALID_PHYSICS_MARKERS, PACKAGE,
    PAYLOAD_SCHEMA, contains_marker, finite_float, is_placeholder,
    load_expected, norm, safe_existing_file, sha256_file, valid_sha256,
    valid_utc,
)
from dmde_v0920_compare_refinement import compare_refinement
from dmde_v0920_validate_bridge_bundle import validate_bridge
from dmde_v0920_validate_raw_evidence import validate_raw_evidence

REQ = [
    "blind_id", "run_timestamp_utc", "backend_family", "backend_name",
    "backend_version_or_commit", "backend_environment", "backend_code_artifact_sha256",
    "backend_environment_sha256", "controlled_configuration_fingerprint", "nuclear_rate_set",
    "neutron_lifetime_s", "source_card_version", "source_payload_schema",
    "source_package_version", "source_payload_sha256",
    "spectral_source_treatment", "collision_treatment", "oscillation_treatment",
    "n_to_p_rate_treatment", "background_to_bbn_bridge",
    "momentum_bins", "coarse_momentum_bins", "momentum_grid_description",
    "coarse_momentum_grid_description", "bridge_schema_version",
    "bridge_history_file", "bridge_history_sha256", "bridge_metadata_file",
    "bridge_metadata_sha256", "raw_output_bundle_file",
    "raw_output_bundle_sha256", "coarse_bridge_history_file",
    "coarse_bridge_history_sha256", "coarse_bridge_metadata_file",
    "coarse_bridge_metadata_sha256", "coarse_raw_output_bundle_file",
    "coarse_raw_output_bundle_sha256", "convergence_pass",
    "convergence_delta_Yp_abs", "convergence_delta_DH_rel",
    "convergence_delta_Neff_abs", "convergence_lambda_np_integral_rel",
    "convergence_lambda_pn_integral_rel", "convergence_H_integral_rel",
    "convergence_summary", "Yp_model", "DH_x1e5_model", "Neff_CMB_model",
]
OPT = [
    "Yp_energy_only_model", "DH_x1e5_energy_only_model",
    "Neff_CMB_energy_only_model", "DeltaYp_spectral_minus_energy_only",
]
NEGATING_TREATMENT_MARKERS = (
    "omitted", "not used", "unused", "disabled", "energy-only", "energy_only",
    "without collision", "without oscillation", "without mixing", "no collision",
    "no oscillation", "no mixing", "no spectral", "integrated qnu only",
)
CONTROLLED_METADATA_FIELDS = (
    "backend_family", "backend_name", "backend_version_or_commit", "backend_environment",
    "momentum_coordinate_definition", "quadrature_weight_definition",
    "physical_momentum_definition", "time_origin_definition",
    "neutrino_antineutrino_convention", "source_mapping_description",
    "source_endpoint_implementation", "spectral_source_treatment",
    "state_dYdq_definition", "state_normalization_density_definition",
    "state_export_method", "transport_stepper_production_callable",
    "transport_stepper_source_toggle", "operator_probe_command",
    "source_stepper_witness_method", "source_stepper_response_definition",
    "source_stepper_target_policy", "source_stepper_state_units",
    "source_stepper_initial_state_definition", "weak_rate_production_callable",
    "weak_rate_canonical_process_map", "weak_rate_born_sentinel_definition",
    "bbn_consumption_canary_command",
    "collision_treatment", "oscillation_treatment", "momentum_coordinate_kind",
    "weak_rate_processes", "weak_rate_corrections", "n_to_p_process_labels",
    "p_to_n_process_labels", "background_to_bbn_bridge", "nuclear_rate_set",
    "neutron_lifetime_s", "interpolation_policy", "extrapolation_policy",
    "production_or_synthetic",
)


def _hash_link(path, claimed, errors, label):
    digest = norm(claimed).lower()
    if not valid_sha256(digest):
        errors.append(f"{label} SHA-256 invalid")
        return False
    if path is None:
        return False
    if sha256_file(path) != digest:
        errors.append(f"{label} SHA-256 mismatch")
        return False
    return True


def _matches(value, expected, *, atol=1e-12):
    actual = finite_float(value)
    return actual is not None and math.isclose(actual, float(expected), rel_tol=1e-12, abs_tol=atol)


def validate_provider_return(
    provider_csv,
    *,
    base,
    bridge_dir,
    raw_bundle_dir,
    allow_synthetic=False,
):
    base = Path(base)
    bridge_dir = Path(bridge_dir)
    raw_bundle_dir = Path(raw_bundle_dir)
    expected = load_expected(base)
    global_errors = []
    try:
        with Path(provider_csv).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:
        return {"schema": "DMDE-v0.9.20-provider-return-firewall", "status": "FAIL", "global_errors": [f"CSV read failure: {exc}"], "rows": []}
    for column in REQ + OPT:
        if column not in columns:
            global_errors.append(f"missing column: {column}")
    ids = [norm(row.get("blind_id")) for row in rows]
    if len(rows) != len(expected):
        global_errors.append(f"row count {len(rows)} != {len(expected)}")
    if len(ids) != len(set(ids)):
        global_errors.append("duplicate blind IDs")
    if set(ids) != set(expected):
        global_errors.append("blind-ID set mismatch")
    backend_signatures = {
        (norm(row.get("backend_family")), norm(row.get("backend_name")), norm(row.get("backend_version_or_commit")), norm(row.get("backend_environment")))
        for row in rows
    }
    if len(backend_signatures) > 1:
        global_errors.append("all blind cards must use one backend family/name/version/environment descriptor")
    for column in ("backend_code_artifact_sha256", "backend_environment_sha256", "controlled_configuration_fingerprint"):
        values = {norm(row.get(column)).lower() for row in rows}
        if len(values) > 1:
            global_errors.append(f"all blind cards must share one {column}")

    receipts = []
    for row_number, row in enumerate(rows, 2):
        blind_id = norm(row.get("blind_id"))
        errors = []
        warnings = []
        frozen = expected.get(blind_id)
        for column in REQ:
            if column not in columns or is_placeholder(row.get(column)):
                errors.append(f"{column}: blank or placeholder")
        if frozen is None:
            errors.append("unknown blind ID")
        if not valid_utc(row.get("run_timestamp_utc")):
            errors.append("run_timestamp_utc must be ISO-8601 UTC")
        if norm(row.get("source_card_version")) != CARD_SCHEMA:
            errors.append("source_card_version mismatch")
        if norm(row.get("source_payload_schema")) != PAYLOAD_SCHEMA:
            errors.append("source_payload_schema mismatch")
        if norm(row.get("source_package_version")) != PACKAGE:
            errors.append("source_package_version mismatch")
        if frozen and norm(row.get("source_payload_sha256")).lower() != frozen["source_payload_sha256"]:
            errors.append("source payload hash mismatch")
        for key in ("backend_code_artifact_sha256", "backend_environment_sha256", "controlled_configuration_fingerprint"):
            if not valid_sha256(row.get(key)):
                errors.append(f"{key}: invalid lowercase SHA-256")
        if norm(row.get("bridge_schema_version")) != BRIDGE_SCHEMA:
            errors.append("bridge schema mismatch")
        treatment_text = " ".join(norm(row.get(key)).lower() for key in (
            "spectral_source_treatment", "collision_treatment", "oscillation_treatment",
            "n_to_p_rate_treatment", "background_to_bbn_bridge",
        ))
        if any(marker in treatment_text for marker in INVALID_PHYSICS_MARKERS):
            errors.append("invalid source-treatment marker")
        if any(marker in treatment_text for marker in NEGATING_TREATMENT_MARKERS):
            errors.append("negating or disabled treatment marker")
        requirements = (
            ("spectral_source_treatment", ("spectral", "momentum", "distribution")),
            ("collision_treatment", ("collision", "scattering", "redistribution", "integral")),
            ("oscillation_treatment", ("oscillation", "mixing", "flavor", "density matrix")),
            ("n_to_p_rate_treatment", ("spectral", "momentum", "phase-space", "integral", "direct")),
        )
        for key, tokens in requirements:
            text = norm(row.get(key)).lower()
            if not any(token in text for token in tokens) or "disabled" in text:
                errors.append(f"{key}: treatment insufficient")
        if not allow_synthetic:
            for key in (
                "backend_family", "backend_name", "backend_version_or_commit",
                "backend_environment", "nuclear_rate_set", "spectral_source_treatment",
                "collision_treatment", "oscillation_treatment", "n_to_p_rate_treatment",
                "background_to_bbn_bridge",
            ):
                if contains_marker(row.get(key)):
                    errors.append(f"{key}: non-production marker")
        fine_bins = finite_float(row.get("momentum_bins"))
        coarse_bins = finite_float(row.get("coarse_momentum_bins"))
        if fine_bins is None or fine_bins < 21 or fine_bins != round(fine_bins):
            errors.append("momentum_bins must be integer >=21")
        if coarse_bins is None or coarse_bins < 21 or coarse_bins != round(coarse_bins):
            errors.append("coarse_momentum_bins must be integer >=21")
        if fine_bins is not None and coarse_bins is not None and fine_bins <= coarse_bins:
            errors.append("fine momentum_bins must exceed coarse_momentum_bins")
        neutron_lifetime = finite_float(row.get("neutron_lifetime_s"))
        if neutron_lifetime is None or not 800 < neutron_lifetime < 1000:
            errors.append("neutron_lifetime_s broad-range failure")

        paths = {}
        for key, directory in (
            ("bridge_history_file", bridge_dir),
            ("bridge_metadata_file", bridge_dir),
            ("coarse_bridge_history_file", bridge_dir),
            ("coarse_bridge_metadata_file", bridge_dir),
            ("raw_output_bundle_file", raw_bundle_dir),
            ("coarse_raw_output_bundle_file", raw_bundle_dir),
        ):
            paths[key] = safe_existing_file(directory, row.get(key), errors, key)
        hash_pairs = (
            ("bridge_history_file", "bridge_history_sha256", "fine bridge history"),
            ("bridge_metadata_file", "bridge_metadata_sha256", "fine bridge metadata"),
            ("coarse_bridge_history_file", "coarse_bridge_history_sha256", "coarse bridge history"),
            ("coarse_bridge_metadata_file", "coarse_bridge_metadata_sha256", "coarse bridge metadata"),
            ("raw_output_bundle_file", "raw_output_bundle_sha256", "fine raw evidence"),
            ("coarse_raw_output_bundle_file", "coarse_raw_output_bundle_sha256", "coarse raw evidence"),
        )
        links_ok = True
        for path_key, hash_key, label in hash_pairs:
            links_ok = _hash_link(paths[path_key], row.get(hash_key), errors, label) and links_ok

        fine_result = coarse_result = fine_raw = coarse_raw = refinement = None
        control_comparison = {}
        if frozen and links_ok:
            fine_result = validate_bridge(paths["bridge_history_file"], paths["bridge_metadata_file"], frozen, allow_synthetic=allow_synthetic)
            coarse_result = validate_bridge(paths["coarse_bridge_history_file"], paths["coarse_bridge_metadata_file"], frozen, allow_synthetic=allow_synthetic)
            if fine_result["status"] != "PASS":
                errors.append("fine bridge validation failed: " + " | ".join(fine_result["errors"]))
            if coarse_result["status"] != "PASS":
                errors.append("coarse bridge validation failed: " + " | ".join(coarse_result["errors"]))
            if fine_result["status"] == coarse_result["status"] == "PASS":
                if fine_result["metadata"].get("run_role") != "fine":
                    errors.append("fine metadata run_role mismatch")
                if coarse_result["metadata"].get("run_role") != "coarse":
                    errors.append("coarse metadata run_role mismatch")
                for result, role in ((fine_result, "fine"), (coarse_result, "coarse")):
                    meta = result["metadata"]
                    for key in (
                        "backend_family", "backend_name", "backend_version_or_commit",
                        "backend_environment", "nuclear_rate_set", "spectral_source_treatment", "collision_treatment",
                        "oscillation_treatment", "background_to_bbn_bridge",
                    ):
                        if norm(meta.get(key)) != norm(row.get(key)):
                            errors.append(f"{role} metadata/{key} row mismatch")
                    row_grid_key = "momentum_grid_description" if role == "fine" else "coarse_momentum_grid_description"
                    if norm(meta.get("momentum_grid_description")) != norm(row.get(row_grid_key)):
                        errors.append(f"{role} metadata/momentum_grid_description row mismatch")
                fine_meta = fine_result["metadata"]
                coarse_meta = coarse_result["metadata"]
                for key in CONTROLLED_METADATA_FIELDS:
                    if fine_meta.get(key) != coarse_meta.get(key):
                        errors.append(f"coarse/fine controlled metadata mismatch: {key}")
                fine_raw = validate_raw_evidence(
                    paths["raw_output_bundle_file"], paths["bridge_history_file"],
                    paths["bridge_metadata_file"], frozen, expected_run_role="fine",
                    allow_synthetic=allow_synthetic,
                )
                coarse_raw = validate_raw_evidence(
                    paths["coarse_raw_output_bundle_file"], paths["coarse_bridge_history_file"],
                    paths["coarse_bridge_metadata_file"], frozen, expected_run_role="coarse",
                    allow_synthetic=allow_synthetic,
                )
                if fine_raw["status"] != "PASS":
                    errors.append("fine raw-evidence validation failed: " + " | ".join(fine_raw["errors"]))
                if coarse_raw["status"] != "PASS":
                    errors.append("coarse raw-evidence validation failed: " + " | ".join(coarse_raw["errors"]))
                for raw_result, role in ((fine_raw, "fine"), (coarse_raw, "coarse")):
                    if raw_result["status"] == "PASS":
                        contract = raw_result.get("metrics", {})
                        for key in ("backend_family", "backend_name", "backend_version_or_commit"):
                            if norm(contract.get(key)) != norm(row.get(key)):
                                errors.append(f"{role} raw contract/{key} row mismatch")
                        raw_string_map = {
                            "collision_treatment": "collision_treatment",
                            "oscillation_treatment": "oscillation_treatment",
                            "weak_rate_treatment": "n_to_p_rate_treatment",
                            "background_to_bbn_bridge": "background_to_bbn_bridge",
                            "nuclear_rate_set": "nuclear_rate_set",
                            "momentum_grid_description": (
                                "momentum_grid_description" if role == "fine" else "coarse_momentum_grid_description"
                            ),
                        }
                        for metric_key, row_key in raw_string_map.items():
                            if norm(contract.get(metric_key)) != norm(row.get(row_key)):
                                errors.append(f"{role} raw solver/{metric_key} row mismatch")
                        row_bin_key = "momentum_bins" if role == "fine" else "coarse_momentum_bins"
                        if not _matches(row.get(row_bin_key), contract.get("momentum_bins"), atol=0):
                            errors.append(f"{role} raw solver/momentum_bins row mismatch")
                        if not _matches(row.get("neutron_lifetime_s"), contract.get("neutron_lifetime_s"), atol=1e-10):
                            errors.append(f"{role} raw solver/neutron_lifetime_s row mismatch")
                        for metric_key, row_key in (
                            ("backend_code_artifact_sha256", "backend_code_artifact_sha256"),
                            ("backend_environment_sha256", "backend_environment_sha256"),
                            ("controlled_configuration_fingerprint", "controlled_configuration_fingerprint"),
                        ):
                            if norm(contract.get(metric_key)).lower() != norm(row.get(row_key)).lower():
                                errors.append(f"{role} raw/{metric_key} row mismatch")
                        if role == "fine" and norm(contract.get("completed_utc")) != norm(row.get("run_timestamp_utc")):
                            errors.append("run_timestamp_utc disagrees with fine raw completed_utc")
                if fine_raw["status"] == coarse_raw["status"] == "PASS":
                    fine_config = fine_raw.get("metrics", {})
                    coarse_config = coarse_raw.get("metrics", {})
                    fine_fingerprint = fine_config.get("controlled_configuration_fingerprint")
                    coarse_fingerprint = coarse_config.get("controlled_configuration_fingerprint")
                    if not fine_fingerprint or fine_fingerprint != coarse_fingerprint:
                        errors.append("coarse/fine controlled raw configuration fingerprint mismatch")
                    try:
                        control_comparison = {
                            "control_delta_Yp_abs": abs(float(fine_config["standard_model_control_Yp"]) - float(coarse_config["standard_model_control_Yp"])),
                            "control_delta_DH_rel": abs(float(fine_config["standard_model_control_DH_x1e5"]) - float(coarse_config["standard_model_control_DH_x1e5"])) / abs(float(fine_config["standard_model_control_DH_x1e5"])),
                            "control_delta_Neff_abs": abs(float(fine_config["standard_model_control_Neff_CMB"]) - float(coarse_config["standard_model_control_Neff_CMB"])),
                        }
                        if control_comparison["control_delta_Yp_abs"] > 1e-4:
                            errors.append("Standard Model control Yp refinement ceiling failed")
                        if control_comparison["control_delta_DH_rel"] > 5e-3:
                            errors.append("Standard Model control D/H refinement ceiling failed")
                        if control_comparison["control_delta_Neff_abs"] > 1e-3:
                            errors.append("Standard Model control Neff refinement ceiling failed")
                    except (KeyError, TypeError, ValueError, ZeroDivisionError):
                        errors.append("Standard Model control coarse/fine comparison failed")
                refinement = compare_refinement(
                    paths["coarse_bridge_history_file"], paths["bridge_history_file"],
                    coarse_result["metrics"], fine_result["metrics"],
                )
                if refinement["status"] != "PASS":
                    errors.append("machine-derived refinement failed: " + " | ".join(refinement["errors"]))

        calculated = dict(refinement.get("metrics", {})) if refinement else {}
        calculated.update(control_comparison)
        claimed_map = {
            "convergence_delta_Yp_abs": "convergence_delta_Yp_abs",
            "convergence_delta_DH_rel": "convergence_delta_DH_rel",
            "convergence_delta_Neff_abs": "convergence_delta_Neff_abs",
            "convergence_lambda_np_integral_rel": "convergence_lambda_np_integral_rel",
            "convergence_lambda_pn_integral_rel": "convergence_lambda_pn_integral_rel",
            "convergence_H_integral_rel": "convergence_H_integral_rel",
        }
        for column, metric_key in claimed_map.items():
            if metric_key in calculated and not _matches(row.get(column), calculated[metric_key], atol=1e-12):
                errors.append(f"{column} disagrees with machine-derived value")
        convergence_claim = norm(row.get("convergence_pass")).lower()
        if convergence_claim not in {"true", "yes", "1", "pass", "passed"}:
            errors.append("convergence_pass not affirmative")
        if refinement and refinement["status"] != "PASS":
            errors.append("convergence_pass claim contradicted by files")

        fine_metrics = fine_result.get("metrics", {}) if fine_result else {}
        for column, metric in (("Yp_model", "Yp_model"), ("DH_x1e5_model", "DH_x1e5_model"), ("Neff_CMB_model", "Neff_CMB_model")):
            value = finite_float(row.get(column))
            if value is None:
                errors.append(f"{column}: non-finite")
            elif metric in fine_metrics and not math.isclose(value, float(fine_metrics[metric]), rel_tol=1e-12, abs_tol=1e-12):
                errors.append(f"{column} disagrees with fine bridge")
        if fine_bins is not None and fine_metrics and int(fine_bins) != int(fine_metrics.get("momentum_bins", -1)):
            errors.append("momentum_bins disagrees with fine bridge")
        coarse_metrics = coarse_result.get("metrics", {}) if coarse_result else {}
        if coarse_bins is not None and coarse_metrics and int(coarse_bins) != int(coarse_metrics.get("momentum_bins", -1)):
            errors.append("coarse_momentum_bins disagrees with coarse bridge")
        for result, role in ((fine_result, "fine"), (coarse_result, "coarse")):
            if result and result.get("identity") and not _matches(row.get("neutron_lifetime_s"), result["identity"]["neutron_lifetime_s"], atol=1e-10):
                errors.append(f"neutron_lifetime_s disagrees with {role} bridge")

        optional_values = [norm(row.get(column)) for column in OPT]
        energy_gate = "NOT_PROVIDED"
        if any(optional_values) and not all(optional_values):
            errors.append("partial energy-only comparison")
        elif all(optional_values):
            parsed = [finite_float(value) for value in optional_values]
            if any(value is None for value in parsed):
                errors.append("non-finite energy-only comparison")
            else:
                yp_model = finite_float(row.get("Yp_model"))
                yp_energy, _, _, delta_yp_energy = parsed
                if yp_model is None or not math.isclose(yp_model - yp_energy, delta_yp_energy, rel_tol=1e-12, abs_tol=1e-10):
                    errors.append("DeltaYp spectral-minus-energy arithmetic mismatch")
                energy_gate = "PASS" if abs(delta_yp_energy) < 1e-4 else "FAIL"

        receipts.append({
            "row_number": row_number,
            "blind_id": blind_id,
            "status": "PASS" if not errors else "FAIL",
            "fine_bridge_validated": fine_result["status"] if fine_result else "NOT_RUN",
            "coarse_bridge_validated": coarse_result["status"] if coarse_result else "NOT_RUN",
            "fine_raw_evidence_validated": fine_raw["status"] if fine_raw else "NOT_RUN",
            "coarse_raw_evidence_validated": coarse_raw["status"] if coarse_raw else "NOT_RUN",
            "machine_convergence": refinement["status"] if refinement else "NOT_RUN",
            "energy_only_equivalence_gate": energy_gate,
            "controlled_configuration_fingerprint": (
                fine_raw.get("metrics", {}).get("controlled_configuration_fingerprint", "") if fine_raw else ""
            ),
            "backend_code_artifact_sha256": (
                fine_raw.get("metrics", {}).get("backend_code_artifact_sha256", "") if fine_raw else ""
            ),
            "backend_environment_sha256": (
                fine_raw.get("metrics", {}).get("backend_environment_sha256", "") if fine_raw else ""
            ),
            "standard_model_control_Yp": (
                fine_raw.get("metrics", {}).get("standard_model_control_Yp", "") if fine_raw else ""
            ),
            "standard_model_control_DH_x1e5": (
                fine_raw.get("metrics", {}).get("standard_model_control_DH_x1e5", "") if fine_raw else ""
            ),
            "standard_model_control_Neff_CMB": (
                fine_raw.get("metrics", {}).get("standard_model_control_Neff_CMB", "") if fine_raw else ""
            ),
            "errors": "; ".join(errors),
            "warnings": "; ".join(warnings),
            **{key: calculated.get(key, "") for key in claimed_map.values()},
            **{key: calculated.get(key, "") for key in ("control_delta_Yp_abs", "control_delta_DH_rel", "control_delta_Neff_abs")},
            "max_local_history_L1_rel": max((value for key, value in calculated.items() if key.endswith("_history_L1_rel")), default=""),
            "max_local_history_global_rel": max((value for key, value in calculated.items() if key.endswith("_history_max_global_rel")), default=""),
            "max_spectral_moment_L1_rel": max((value for key, value in calculated.items() if "_moment_L1_rel" in key), default=""),
            "max_spectral_moment_global_rel": max((value for key, value in calculated.items() if "_moment_max_global_rel" in key), default=""),
        })

    if len(receipts) == len(expected):
        control_values = {
            key: [finite_float(row.get(key)) for row in receipts]
            for key in ("standard_model_control_Yp", "standard_model_control_DH_x1e5", "standard_model_control_Neff_CMB")
        }
        if all(value is not None for values in control_values.values() for value in values):
            if max(control_values["standard_model_control_Yp"]) - min(control_values["standard_model_control_Yp"]) > 1e-4:
                global_errors.append("cross-card Standard Model control Yp mismatch")
            dh_values = control_values["standard_model_control_DH_x1e5"]
            if (max(dh_values) - min(dh_values)) / max(abs(value) for value in dh_values) > 5e-3:
                global_errors.append("cross-card Standard Model control D/H mismatch")
            if max(control_values["standard_model_control_Neff_CMB"]) - min(control_values["standard_model_control_Neff_CMB"]) > 1e-3:
                global_errors.append("cross-card Standard Model control Neff mismatch")
        else:
            global_errors.append("cross-card Standard Model control comparison unavailable")
    status = "PASS" if not global_errors and receipts and all(row["status"] == "PASS" for row in receipts) else "FAIL"
    return {
        "schema": "DMDE-v0.9.20-provider-return-firewall",
        "status": status,
        "global_errors": global_errors,
        "rows": receipts,
        "allow_synthetic_test_mode": bool(allow_synthetic),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("provider_csv")
    parser.add_argument("--base", default=".")
    parser.add_argument("--bridge-dir", required=True)
    parser.add_argument("--raw-bundle-dir", required=True)
    parser.add_argument("--out-csv", default="DMDE_v0920_provider_return_validation.csv")
    parser.add_argument("--out-json", default="DMDE_v0920_provider_return_validation.json")
    args = parser.parse_args()
    result = validate_provider_return(
        args.provider_csv, base=args.base, bridge_dir=args.bridge_dir,
        raw_bundle_dir=args.raw_bundle_dir, allow_synthetic=False,
    )
    rows = result["rows"]
    fields = list(rows[0]) if rows else ["row_number", "blind_id", "status", "errors"]
    with Path(args.out_csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PROVIDER RETURN VALIDATION {result['status']}: {len(rows)} row(s)")
    for error in result["global_errors"]:
        print("GLOBAL:", error)
    for row in rows:
        if row["status"] != "PASS":
            print(row["blind_id"], row["errors"])
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
