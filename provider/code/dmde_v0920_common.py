#!/usr/bin/env python3
"""Shared constants and fail-closed helpers for the DMDE v0.9.20 bridge draft."""
from __future__ import annotations

import csv
import hashlib
import math
import re
from pathlib import Path

BRIDGE_SCHEMA = "DMDE-SPECTRAL-BBN-BRIDGE-v0.9.20"
# v0.9.20 coordinates the bridge and raw contracts so operator, weak-rate,
# and BBN-consumption witnesses are bound into one fail-closed return path.
RAW_SCHEMA = "DMDE-RAW-EVIDENCE-CONTRACT-v0.9.20"
PACKAGE = "DMDE-v0.9.20-provider-dispatch-source-frozen"
CARD_SCHEMA = "DMDE-SPECTRAL-SOURCE-CARD-v0.9.4"
PAYLOAD_SCHEMA = "DMDE-SPECTRAL-SEPARABLE-PAYLOAD-v0.9.8"
EXPECTED_TABLE = "DMDE_v0920_expected_source_identities.csv"

PLACEHOLDERS = {
    "", "na", "n/a", "none", "null", "unknown", "tbd", "todo",
    "pending", "placeholder", "fill", "-", "?"
}
NONPRODUCTION_MARKERS = (
    "synthetic", "mock", "fixture", "test-only", "test_only", "example",
    "demonstration only", "software test", "dummy"
)
INVALID_PHYSICS_MARKERS = (
    "energy-only", "energy_only", "negative dark radiation",
    "negative_dark_radiation", "thermal qnu only", "integrated qnu only"
)
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def norm(value) -> str:
    return str(value if value is not None else "").strip()


def is_placeholder(value) -> bool:
    text = norm(value).lower()
    return text in PLACEHOLDERS or text.startswith(
        ("fill_", "fill ", "<fill", "replace_", "replace ")
    )


def finite_float(value):
    try:
        result = float(norm(value))
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_expected(base: Path) -> dict[str, dict[str, str]]:
    path = base / "tables" / EXPECTED_TABLE
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {norm(row.get("blind_id")): row for row in rows}
    if not rows or len(result) != len(rows) or any(not key for key in result):
        raise ValueError(f"invalid frozen identity table: {path}")
    return result


def close_float(actual, expected, *, rtol=2e-13, atol=1e-15) -> bool:
    return math.isclose(float(actual), float(expected), rel_tol=rtol, abs_tol=atol)


def safe_existing_file(base: Path, relative_name: str, errors: list[str], label: str):
    """Resolve an untrusted relative filename without allowing escape or symlinks."""
    candidate = Path(norm(relative_name))
    if not candidate.parts or candidate.is_absolute() or ".." in candidate.parts:
        errors.append(f"{label}: must be a nonempty relative path without '..'")
        return None
    try:
        root = base.resolve(strict=True)
    except FileNotFoundError:
        errors.append(f"{label}: base directory missing")
        return None
    current = root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            errors.append(f"{label}: symbolic links are forbidden")
            return None
    try:
        resolved = current.resolve(strict=True)
    except FileNotFoundError:
        errors.append(f"{label}: file missing")
        return None
    try:
        resolved.relative_to(root)
    except ValueError:
        errors.append(f"{label}: resolved path escapes its base directory")
        return None
    if not resolved.is_file():
        errors.append(f"{label}: not a regular file")
        return None
    return resolved


def contains_marker(value, markers=NONPRODUCTION_MARKERS) -> bool:
    text = norm(value).lower()
    return any(marker in text for marker in markers)


def valid_sha256(value) -> bool:
    return bool(SHA256_RE.fullmatch(norm(value).lower()))


def valid_utc(value) -> bool:
    return bool(UTC_RE.fullmatch(norm(value)))
