#!/usr/bin/env python3
"""Validate the DMDE v0.9.20 BBN-input consumption canary.

The contract proves byte identity for a baseline replay and checks four exact
derived weak-rate inputs.  Signed, above-noise, near-linear Yp responses show
that the declared BBN execution path consumed the supplied n<->p histories.
This is an execution canary, not a validation of the nuclear network itself.
"""
from __future__ import annotations

import argparse
import csv
import io
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
    verify_file_ref,
)


SCHEMA_VERSION = "DMDE-BBN-CONSUMPTION-CANARY-v0.9.20"
WINDOW_T_MIN_MEV = 0.5
WINDOW_T_MAX_MEV = 1.2
RATIO_MIN = 1.5
RATIO_MAX = 2.5

RATE_COLUMNS = [
    "time_s",
    "T_gamma_MeV",
    "H_s_inv",
    "lambda_n_to_p_s_inv",
    "lambda_p_to_n_s_inv",
]
SUMMARY_COLUMNS = [
    "run_id",
    "rate_field",
    "perturbation_fraction",
    "T_gamma_min_MeV",
    "T_gamma_max_MeV",
    "input_sha256",
    "output_sha256",
    "Yp_model",
    "DeltaYp",
]

EXPECTED_RUNS = {
    "np_plus_1pct": ("lambda_n_to_p_s_inv", 0.01),
    "np_plus_0p5pct": ("lambda_n_to_p_s_inv", 0.005),
    "pn_plus_1pct": ("lambda_p_to_n_s_inv", 0.01),
    "pn_plus_0p5pct": ("lambda_p_to_n_s_inv", 0.005),
}
SUMMARY_ORDER = ["baseline", *EXPECTED_RUNS]

TOP_KEYS = {
    "schema_version",
    "code",
    "config",
    "production",
    "baseline_replay",
    "canary_summary",
    "deterministic_noise_floor_Yp",
    "runs",
}
PAIR_KEYS = {"rate_input", "output"}
RUN_KEYS = {
    "run_id",
    "rate_field",
    "perturbation_fraction",
    "T_gamma_min_MeV",
    "T_gamma_max_MeV",
    "rate_input",
    "output",
}


def _read_csv(path: Path, expected_columns: list[str], *, label: str) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != expected_columns:
            raise ContractError(f"{label}: exact header mismatch")
        rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"{label}: CSV parse failure: {exc}") from exc
    if not rows:
        raise ContractError(f"{label}: at least one data row required")
    for index, row in enumerate(rows, start=2):
        if None in row or any(row.get(column) is None for column in expected_columns):
            raise ContractError(f"{label} row {index}: wrong field count")
    return rows


def _parse_rate_input(path: Path, *, label: str) -> dict[str, np.ndarray]:
    rows = _read_csv(path, RATE_COLUMNS, label=label)
    columns: dict[str, np.ndarray] = {}
    for column in RATE_COLUMNS:
        parsed = []
        for index, row in enumerate(rows, start=2):
            parsed.append(finite_float(row[column], label=f"{label} row {index} {column}"))
        columns[column] = np.asarray(parsed, dtype=float)
    if len(rows) < 3:
        raise ContractError(f"{label}: at least three history rows required")
    if columns["time_s"][0] < 0 or np.any(np.diff(columns["time_s"]) <= 0):
        raise ContractError(f"{label}: nonnegative strictly increasing time required")
    if (
        np.any(columns["T_gamma_MeV"] <= 0)
        or np.any(columns["H_s_inv"] <= 0)
        or np.any(columns["lambda_n_to_p_s_inv"] <= 0)
        or np.any(columns["lambda_p_to_n_s_inv"] < 0)
    ):
        raise ContractError(f"{label}: positive T/H/lambda_np and nonnegative lambda_pn required")
    return columns


def _yp_from_output(path: Path, *, label: str) -> float:
    value = load_json_object(path, label=label)
    if "Yp_model" not in value:
        raise ContractError(f"{label}: Yp_model missing")
    yp = finite_float(value["Yp_model"], label=f"{label}.Yp_model")
    if not 0 < yp < 1:
        raise ContractError(f"{label}.Yp_model: physical mass fraction required")
    return yp


def _same_numeric_columns(left: dict[str, np.ndarray], right: dict[str, np.ndarray], columns: list[str]) -> bool:
    return all(np.array_equal(left[column], right[column]) for column in columns)


def _validate_derived_input(
    baseline: dict[str, np.ndarray],
    derived: dict[str, np.ndarray],
    *,
    rate_field: str,
    fraction: float,
    label: str,
) -> dict[str, int]:
    lengths = {len(values) for values in [*baseline.values(), *derived.values()]}
    if len(lengths) != 1:
        raise ContractError(f"{label}: row count disagrees with baseline")
    unchanged = [column for column in RATE_COLUMNS if column != rate_field]
    if not _same_numeric_columns(baseline, derived, unchanged):
        raise ContractError(f"{label}: a non-target column differs from baseline")
    temperature = baseline["T_gamma_MeV"]
    in_window = (temperature >= WINDOW_T_MIN_MEV) & (temperature <= WINDOW_T_MAX_MEV)
    if not np.any(in_window) or not np.any(~in_window):
        raise ContractError(f"{label}: baseline must contain nodes both inside and outside the canary window")
    expected = baseline[rate_field].copy()
    expected[in_window] *= 1.0 + fraction
    actual = derived[rate_field]
    tolerance = np.maximum(np.abs(expected) * 2e-13, 1e-300)
    if np.any(np.abs(actual - expected) > tolerance):
        bad_inside = int(np.count_nonzero(np.abs(actual[in_window] - expected[in_window]) > tolerance[in_window]))
        bad_outside = int(np.count_nonzero(np.abs(actual[~in_window] - expected[~in_window]) > tolerance[~in_window]))
        raise ContractError(
            f"{label}: input is not the exact +{fraction:g} target-rate derivation "
            f"inside 1.2>=T_gamma>=0.5 MeV (bad_inside={bad_inside}, bad_outside={bad_outside})"
        )
    return {"window_rows": int(np.count_nonzero(in_window)), "outside_rows": int(np.count_nonzero(~in_window))}


def _parse_pair(root: Path, value: Any, *, label: str) -> tuple[Path, Path]:
    exact_keys(value, PAIR_KEYS, label=label)
    rate_input = verify_file_ref(root, value["rate_input"], label=f"{label}.rate_input")
    output = verify_file_ref(root, value["output"], label=f"{label}.output")
    return rate_input, output


def _summary_rows(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv(path, SUMMARY_COLUMNS, label="canary summary")
    ids = [row["run_id"] for row in rows]
    if ids != SUMMARY_ORDER:
        raise ContractError("canary summary: exact canonical row order/set required")
    return {row["run_id"]: row for row in rows}


def validate_bbn_canary(contract_path: Path | str) -> dict[str, Any]:
    contract_path = Path(contract_path)
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    if not contract_path.is_file() or contract_path.is_symlink():
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": ["BBN canary contract missing or unsafe"], "metrics": {}}
    root = contract_path.parent
    try:
        contract = load_json_object(contract_path, label="BBN canary contract")
        exact_keys(contract, TOP_KEYS, label="BBN canary contract")
        if contract["schema_version"] != SCHEMA_VERSION:
            raise ContractError("BBN canary contract schema_version mismatch")
        verify_file_ref(root, contract["code"], label="code")
        verify_file_ref(root, contract["config"], label="config")
        production_input_path, production_output_path = _parse_pair(root, contract["production"], label="production")
        baseline_input_path, baseline_output_path = _parse_pair(root, contract["baseline_replay"], label="baseline_replay")
        summary_path = verify_file_ref(root, contract["canary_summary"], label="canary_summary")
        noise_floor = finite_float(contract["deterministic_noise_floor_Yp"], label="deterministic_noise_floor_Yp")
        if not 0 < noise_floor < 1e-3:
            raise ContractError("deterministic_noise_floor_Yp must lie strictly between 0 and 1e-3")

        if production_input_path.read_bytes() != baseline_input_path.read_bytes():
            raise ContractError("baseline replay rate input is not byte-identical to production BBN input")
        if production_output_path.read_bytes() != baseline_output_path.read_bytes():
            raise ContractError("baseline replay output is not byte-identical to production BBN output")
        baseline_input = _parse_rate_input(baseline_input_path, label="baseline replay rate input")
        baseline_yp = _yp_from_output(baseline_output_path, label="baseline replay output")
        metrics.update({
            "baseline_input_sha256": sha256_file(baseline_input_path),
            "baseline_output_sha256": sha256_file(baseline_output_path),
            "baseline_Yp_model": baseline_yp,
            "deterministic_noise_floor_Yp": noise_floor,
        })

        runs = contract["runs"]
        if not isinstance(runs, list) or len(runs) != len(EXPECTED_RUNS):
            raise ContractError("runs: exactly four canonical canary runs required")
        run_map: dict[str, dict[str, Any]] = {}
        run_paths: dict[str, tuple[Path, Path]] = {}
        run_yps: dict[str, float] = {}
        for index, run in enumerate(runs):
            label = f"runs[{index}]"
            exact_keys(run, RUN_KEYS, label=label)
            run_id = run["run_id"]
            if run_id not in EXPECTED_RUNS or run_id in run_map:
                raise ContractError(f"{label}.run_id: unknown or duplicate canonical run")
            wanted_field, wanted_fraction = EXPECTED_RUNS[run_id]
            if run["rate_field"] != wanted_field:
                raise ContractError(f"{label}.rate_field: canonical target mismatch")
            fraction = finite_float(run["perturbation_fraction"], label=f"{label}.perturbation_fraction")
            if fraction != wanted_fraction:
                raise ContractError(f"{label}.perturbation_fraction: exact canonical fraction required")
            t_min = finite_float(run["T_gamma_min_MeV"], label=f"{label}.T_gamma_min_MeV")
            t_max = finite_float(run["T_gamma_max_MeV"], label=f"{label}.T_gamma_max_MeV")
            if t_min != WINDOW_T_MIN_MEV or t_max != WINDOW_T_MAX_MEV:
                raise ContractError(f"{label}: exact 0.5..1.2 MeV canary window required")
            input_path = verify_file_ref(root, run["rate_input"], label=f"{label}.rate_input")
            output_path = verify_file_ref(root, run["output"], label=f"{label}.output")
            derived_input = _parse_rate_input(input_path, label=f"{run_id} rate input")
            counts = _validate_derived_input(
                baseline_input,
                derived_input,
                rate_field=wanted_field,
                fraction=wanted_fraction,
                label=run_id,
            )
            run_yp = _yp_from_output(output_path, label=f"{run_id} output")
            run_map[run_id] = run
            run_paths[run_id] = (input_path, output_path)
            run_yps[run_id] = run_yp
            metrics[f"{run_id}_window_rows"] = counts["window_rows"]
            metrics[f"{run_id}_Yp_model"] = run_yp

        if list(run_map) != list(EXPECTED_RUNS):
            raise ContractError("runs: exact canonical order required")

        summary = _summary_rows(summary_path)
        baseline_summary = summary["baseline"]
        if baseline_summary["rate_field"] != "none":
            raise ContractError("canary summary baseline rate_field must equal none")
        baseline_fraction = finite_float(baseline_summary["perturbation_fraction"], label="summary baseline perturbation_fraction")
        if baseline_fraction != 0:
            raise ContractError("canary summary baseline perturbation_fraction must be zero")
        if (
            finite_float(baseline_summary["T_gamma_min_MeV"], label="summary baseline T_gamma_min_MeV")
            != WINDOW_T_MIN_MEV
            or finite_float(baseline_summary["T_gamma_max_MeV"], label="summary baseline T_gamma_max_MeV")
            != WINDOW_T_MAX_MEV
        ):
            raise ContractError("canary summary baseline window mismatch")
        for key, wanted in (
            ("input_sha256", sha256_file(baseline_input_path)),
            ("output_sha256", sha256_file(baseline_output_path)),
        ):
            if baseline_summary[key] != wanted:
                raise ContractError(f"canary summary baseline {key} mismatch")
        if not math.isclose(finite_float(baseline_summary["Yp_model"], label="summary baseline Yp_model"), baseline_yp, rel_tol=0, abs_tol=1e-14):
            raise ContractError("canary summary baseline Yp_model mismatch")
        if finite_float(baseline_summary["DeltaYp"], label="summary baseline DeltaYp") != 0:
            raise ContractError("canary summary baseline DeltaYp must be zero")

        deltas: dict[str, float] = {}
        for run_id, (wanted_field, wanted_fraction) in EXPECTED_RUNS.items():
            row = summary[run_id]
            run = run_map[run_id]
            input_path, output_path = run_paths[run_id]
            if row["rate_field"] != wanted_field:
                raise ContractError(f"canary summary {run_id}: rate_field mismatch")
            if finite_float(row["perturbation_fraction"], label=f"summary {run_id} perturbation_fraction") != wanted_fraction:
                raise ContractError(f"canary summary {run_id}: perturbation_fraction mismatch")
            if finite_float(row["T_gamma_min_MeV"], label=f"summary {run_id} T_gamma_min_MeV") != WINDOW_T_MIN_MEV or finite_float(row["T_gamma_max_MeV"], label=f"summary {run_id} T_gamma_max_MeV") != WINDOW_T_MAX_MEV:
                raise ContractError(f"canary summary {run_id}: window mismatch")
            if row["input_sha256"] != sha256_file(input_path) or row["output_sha256"] != sha256_file(output_path):
                raise ContractError(f"canary summary {run_id}: input/output hash mismatch")
            yp = run_yps[run_id]
            delta = yp - baseline_yp
            if not math.isclose(finite_float(row["Yp_model"], label=f"summary {run_id} Yp_model"), yp, rel_tol=0, abs_tol=1e-14):
                raise ContractError(f"canary summary {run_id}: Yp_model mismatch")
            if not math.isclose(finite_float(row["DeltaYp"], label=f"summary {run_id} DeltaYp"), delta, rel_tol=0, abs_tol=1e-14):
                raise ContractError(f"canary summary {run_id}: DeltaYp arithmetic mismatch")
            deltas[run_id] = delta
            metrics[f"{run_id}_DeltaYp"] = delta

        for run_id in ("np_plus_1pct", "np_plus_0p5pct"):
            if deltas[run_id] >= -noise_floor:
                raise ContractError(f"{run_id}: DeltaYp must be negative and exceed deterministic noise floor")
        for run_id in ("pn_plus_1pct", "pn_plus_0p5pct"):
            if deltas[run_id] <= noise_floor:
                raise ContractError(f"{run_id}: DeltaYp must be positive and exceed deterministic noise floor")

        np_ratio = abs(deltas["np_plus_1pct"] / deltas["np_plus_0p5pct"])
        pn_ratio = abs(deltas["pn_plus_1pct"] / deltas["pn_plus_0p5pct"])
        metrics["np_response_ratio_1pct_over_0p5pct"] = np_ratio
        metrics["pn_response_ratio_1pct_over_0p5pct"] = pn_ratio
        if not RATIO_MIN <= np_ratio <= RATIO_MAX:
            raise ContractError("lambda_np canary response ratio is outside 1.5..2.5")
        if not RATIO_MIN <= pn_ratio <= RATIO_MAX:
            raise ContractError("lambda_pn canary response ratio is outside 1.5..2.5")
    except (ContractError, OSError) as exc:
        errors.append(str(exc))

    return {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract_json")
    parser.add_argument("--out-json")
    args = parser.parse_args()
    result = validate_bbn_canary(args.contract_json)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out_json:
        Path(args.out_json).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
