#!/usr/bin/env python3
"""Meaningful two-dimensional refinement checks for DMDE bridge histories."""
from __future__ import annotations

import argparse
import bisect
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

SOURCE_LIFETIMES = 18.0
WEAK_T_HIGH_MEV = 1.2
WEAK_T_LOW_MEV = 0.5
M_E_MEV = 0.51099895
DELTA_NP_MEV = 1.29333236
ANTINU_THRESHOLD_MEV = M_E_MEV + DELTA_NP_MEV
BETA_ENDPOINT_MEV = DELTA_NP_MEV - M_E_MEV
M_MU_MEV = 105.6583755
SOURCE_ENDPOINT_MEV = M_MU_MEV / 2.0
DEFAULT_MIN_REDUCTION = 0.10


def _floats(values: Sequence[float], label: str) -> tuple[float, ...]:
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: nonnumeric sequence") from exc
    if not result or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{label}: nonempty finite sequence required")
    return result


def _strictly_increasing(values: Sequence[float]) -> bool:
    return all(right > left for left, right in zip(values, values[1:]))


def _source_max_dt_over_tau(t: tuple[float, ...], tau: float) -> float:
    cutoff = SOURCE_LIFETIMES * tau
    spans = []
    for left, right in zip(t, t[1:]):
        overlap = min(right, cutoff) - max(left, 0.0)
        if overlap > 0:
            spans.append(overlap / tau)
    if not spans or t[0] > 0 or t[-1] < cutoff:
        raise ValueError("time history does not cover the complete source window [0,18 tau]")
    return max(spans)


def _weak_max_abs_dlnT(temperature: tuple[float, ...]) -> float:
    if min(temperature) > WEAK_T_LOW_MEV or max(temperature) < WEAK_T_HIGH_MEV:
        raise ValueError("temperature history does not span 1.2 to 0.5 MeV")
    spans = []
    for left, right in zip(temperature, temperature[1:]):
        segment_low = max(min(left, right), WEAK_T_LOW_MEV)
        segment_high = min(max(left, right), WEAK_T_HIGH_MEV)
        if segment_high > segment_low:
            spans.append(math.log(segment_high / segment_low))
    if not spans:
        raise ValueError("no temperature interval intersects the 1.2 to 0.5 MeV window")
    return max(spans)


def _threshold_bracket_width(
    q: tuple[float, ...], pscale: float, threshold: float, label: str
) -> float:
    physical = tuple(value * pscale for value in q)
    if threshold < physical[0] or threshold > physical[-1]:
        raise ValueError(f"physical momentum grid does not bracket the {label}")
    index = bisect.bisect_left(physical, threshold)
    if index == 0:
        return physical[1] - physical[0]
    if index == len(physical):
        return physical[-1] - physical[-2]
    if math.isclose(physical[index], threshold, rel_tol=0.0, abs_tol=1e-14):
        widths = [physical[index] - physical[index - 1]]
        if index + 1 < len(physical):
            widths.append(physical[index + 1] - physical[index])
        # An exact threshold node must not hide a coarse cell on either side.
        return max(widths)
    return physical[index] - physical[index - 1]


def _source_domain_max_cell_width(q: tuple[float, ...], pscale: float) -> float:
    """Largest physical cell overlapping 0 <= p <= m_mu/2."""
    physical = tuple(value * pscale for value in q)
    if physical[-1] < SOURCE_ENDPOINT_MEV:
        raise ValueError("physical momentum grid does not cover the stopped-muon endpoint")
    widths = []
    if physical[0] > 0:
        widths.append(min(physical[0], SOURCE_ENDPOINT_MEV))
    for left, right in zip(physical, physical[1:]):
        overlap = min(right, SOURCE_ENDPOINT_MEV) - max(left, 0.0)
        if overlap > 0:
            widths.append(overlap)
    if not widths:
        raise ValueError("physical momentum grid has no cells in the stopped-muon source domain")
    return max(widths)


def grid_metrics(history: Mapping[str, object]) -> dict[str, float | int]:
    t = _floats(history["t_s"], "t_s")
    temperature = _floats(history["T_gamma_MeV"], "T_gamma_MeV")
    q = _floats(history["q_grid"], "q_grid")
    pscale = _floats(history["p_per_q_MeV"], "p_per_q_MeV")
    tau = float(history["tau_s"])
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError("tau_s must be finite and positive")
    if len(t) != len(temperature) or len(t) != len(pscale):
        raise ValueError("time, temperature, and p_per_q histories must have equal length")
    if len(t) < 2 or len(q) < 2 or not _strictly_increasing(t) or not _strictly_increasing(q):
        raise ValueError("time and momentum grids must be strictly increasing with at least two nodes")
    if any(value <= 0 for value in temperature + pscale) or any(value < 0 for value in q):
        raise ValueError("temperature and momentum values must be positive (q may start at zero)")

    cutoff = SOURCE_LIFETIMES * tau
    active_scales = [scale for time, scale in zip(t, pscale) if time <= cutoff]
    if not active_scales:
        raise ValueError("no momentum scale in source window")
    max_cell_width = max(_source_domain_max_cell_width(q, scale) for scale in active_scales)
    max_threshold_width = max(
        _threshold_bracket_width(q, scale, ANTINU_THRESHOLD_MEV, "antineutrino threshold")
        for scale in pscale
    )
    max_beta_endpoint_width = max(
        _threshold_bracket_width(q, scale, BETA_ENDPOINT_MEV, "beta-decay endpoint")
        for scale in pscale
    )
    return {
        "Nt": len(t),
        "Nq": len(q),
        "source_max_dt_over_tau": _source_max_dt_over_tau(t, tau),
        "weak_max_abs_dlnT_1p2_to_0p5": _weak_max_abs_dlnT(temperature),
        "source_domain_max_physical_cell_width_MeV": max_cell_width,
        "antinu_threshold_max_bracket_width_MeV": max_threshold_width,
        "beta_endpoint_max_bracket_width_MeV": max_beta_endpoint_width,
    }


def evaluate_meaningful_refinement(
    coarse: Mapping[str, object],
    fine: Mapping[str, object],
    min_reduction: float = DEFAULT_MIN_REDUCTION,
) -> dict[str, object]:
    if not 0 < min_reduction < 1:
        raise ValueError("min_reduction must lie strictly between zero and one")
    coarse_tau = float(coarse["tau_s"])
    fine_tau = float(fine["tau_s"])
    if not math.isclose(coarse_tau, fine_tau, rel_tol=1e-13, abs_tol=1e-15):
        raise ValueError("coarse/fine tau_s mismatch")
    coarse_metrics = grid_metrics(coarse)
    fine_metrics = grid_metrics(fine)

    checks: dict[str, bool] = {
        "fine_Nt_strictly_greater": fine_metrics["Nt"] > coarse_metrics["Nt"],
        "fine_Nq_strictly_greater": fine_metrics["Nq"] > coarse_metrics["Nq"],
    }
    ratios: dict[str, float] = {}
    for key in (
        "source_max_dt_over_tau",
        "weak_max_abs_dlnT_1p2_to_0p5",
        "source_domain_max_physical_cell_width_MeV",
        "antinu_threshold_max_bracket_width_MeV",
        "beta_endpoint_max_bracket_width_MeV",
    ):
        coarse_value = float(coarse_metrics[key])
        fine_value = float(fine_metrics[key])
        ratio = fine_value / coarse_value
        ratios[f"fine_over_coarse_{key}"] = ratio
        checks[f"{key}_reduced_by_at_least_{min_reduction:.0%}"] = (
            ratio <= (1.0 - min_reduction) * (1.0 + 1e-12)
        )
    errors = [name for name, passed in checks.items() if not passed]
    return {
        "schema": "DMDE-v0.9.20-meaningful-refinement-v1",
        "status": "PASS" if not errors else "FAIL",
        "minimum_required_reduction": min_reduction,
        "coarse": coarse_metrics,
        "fine": fine_metrics,
        "ratios": ratios,
        "checks": checks,
        "failed_checks": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("coarse_json")
    parser.add_argument("fine_json")
    parser.add_argument("--min-reduction", type=float, default=DEFAULT_MIN_REDUCTION)
    parser.add_argument("--out-json")
    args = parser.parse_args()
    coarse = json.loads(Path(args.coarse_json).read_text(encoding="utf-8"))
    fine = json.loads(Path(args.fine_json).read_text(encoding="utf-8"))
    result = evaluate_meaningful_refinement(coarse, fine, args.min_reduction)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out_json:
        Path(args.out_json).write_text(output, encoding="utf-8")
    print(output, end="")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
