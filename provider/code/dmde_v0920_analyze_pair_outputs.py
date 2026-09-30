#!/usr/bin/env python3
"""Analyze validated DMDE endpoint outputs using the frozen-pair geometry.

The program calculates log secants and propagates a user-supplied numerical
error bound.  Passing this program is not a physics-validation claim; the
input outputs must first pass the full provider-return contract.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


EXPECTED = {
    "low": {
        "blind_id": "DMDE-SPEC-V099-4Q7N",
        "source_payload_sha256": "f5f9ad03206572f12103655714cf5c814287ba07dd45bdc3c6185312a3553dcb",
    },
    "high": {
        "blind_id": "DMDE-SPEC-V099-8M2K",
        "source_payload_sha256": "ad86c5d4161afd12dde76e83bb19c9b313197fc31703baaf00cad7ba9f478c3e",
    },
}
OUTPUT_FIELDS = ("Yp_model", "DH_x1e5_model", "Neff_CMB_model")


class AnalysisError(ValueError):
    pass


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AnalysisError(f"{path}: JSON object required")
    return value


def validate_endpoint(value: dict[str, Any], role: str) -> None:
    for key, wanted in EXPECTED[role].items():
        if value.get(key) != wanted:
            raise AnalysisError(f"{role}: {key} mismatch")
    for field in OUTPUT_FIELDS:
        try:
            number = float(value[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(f"{role}: positive finite {field} required") from exc
        if not math.isfinite(number) or number <= 0.0:
            raise AnalysisError(f"{role}: positive finite {field} required")


def analyze(
    low: dict[str, Any],
    high: dict[str, Any],
    geometry: dict[str, Any],
    endpoint_log_error_bound: float,
    em_elasticity_bound: float | None,
) -> dict[str, Any]:
    validate_endpoint(low, "low")
    validate_endpoint(high, "high")
    if endpoint_log_error_bound < 0.0 or not math.isfinite(endpoint_log_error_bound):
        raise AnalysisError("endpoint log-error bound must be finite and nonnegative")
    if em_elasticity_bound is not None and (
        em_elasticity_bound < 0.0 or not math.isfinite(em_elasticity_bound)
    ):
        raise AnalysisError("EM elasticity bound must be finite and nonnegative")

    try:
        source = geometry["log_source_geometry"]
        du = float(source["delta_ln_nu_amplitude"])
        rho = abs(float(source["em_to_nu_log_contrast_ratio_rho"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisError("invalid geometry receipt") from exc
    if not math.isfinite(du) or du <= 0.0 or not math.isfinite(rho):
        raise AnalysisError("invalid geometry constants")

    numerical_bound = 2.0 * endpoint_log_error_bound / du
    nuisance_bound = None if em_elasticity_bound is None else rho * em_elasticity_bound
    outputs: dict[str, Any] = {}
    for field in OUTPUT_FIELDS:
        low_value = float(low[field])
        high_value = float(high[field])
        log_contrast = math.log(high_value / low_value)
        outputs[field] = {
            "low": low_value,
            "high": high_value,
            "log_output_contrast": log_contrast,
            "pair_averaged_directional_log_elasticity": log_contrast / du,
            "worst_case_absolute_elasticity_error_from_declared_endpoint_numerics": numerical_bound,
            "conditional_em_nuisance_absolute_elasticity_bound": nuisance_bound,
        }

    return {
        "schema": "DMDE-FROZEN-PAIR-OUTPUT-ANALYSIS-v0.9.20",
        "status": "CALCULATED_NOT_PHYSICS_VALIDATED",
        "prerequisite": "Both endpoint returns must independently pass the complete v0.9.20 provider-return validation before interpretation.",
        "delta_ln_nu_amplitude": du,
        "rho": rho,
        "declared_each_endpoint_log_output_error_bound": endpoint_log_error_bound,
        "declared_em_log_elasticity_bound": em_elasticity_bound,
        "outputs": outputs,
        "interpretation_limit": "Each value is the path-averaged full neutrino-injection directional elasticity plus rho times the path-averaged EM elasticity. It is not a local, weak-kernel-only, or abundance-discovery result.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--low-json", type=Path, required=True)
    parser.add_argument("--high-json", type=Path, required=True)
    parser.add_argument("--geometry-json", type=Path, required=True)
    parser.add_argument("--endpoint-log-error-bound", type=float, required=True)
    parser.add_argument("--em-elasticity-bound", type=float)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze(
        load_object(args.low_json),
        load_object(args.high_json),
        load_object(args.geometry_json),
        args.endpoint_log_error_bound,
        args.em_elasticity_bound,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
