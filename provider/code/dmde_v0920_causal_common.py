#!/usr/bin/env python3
"""Fail-closed helpers shared by the DMDE v0.9.20 causal validators."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


SHA256_RE = re.compile(r"[0-9a-f]{64}")


class ContractError(ValueError):
    """Raised when untrusted contract material is malformed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def finite_float(value: Any, *, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label}: numeric value required") from exc
    if not math.isfinite(result):
        raise ContractError(f"{label}: finite value required")
    return result


def _no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractError(f"{label}: non-finite JSON constant {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError(f"{label}: JSON parse failure: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label}: JSON root must be an object")
    return value


def exact_keys(value: Any, required: set[str], *, label: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{label}: object required")
    actual = set(value)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ContractError(f"{label}: exact-key failure ({'; '.join(details)})")


def safe_relative_file(root: Path, name: Any, *, label: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ContractError(f"{label}: nonempty POSIX relative path required")
    candidate = Path(name)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ContractError(f"{label}: unsafe relative path")
    resolved_root = root.resolve(strict=True)
    current = resolved_root
    for part in candidate.parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(f"{label}: symbolic links are forbidden")
    try:
        resolved = current.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ContractError(f"{label}: file missing") from exc
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractError(f"{label}: path escapes contract root") from exc
    if not resolved.is_file():
        raise ContractError(f"{label}: regular file required")
    return resolved


def verify_file_ref(root: Path, value: Any, *, label: str) -> Path:
    exact_keys(value, {"path", "sha256"}, label=label)
    if not valid_sha256(value["sha256"]):
        raise ContractError(f"{label}.sha256: lowercase SHA-256 required")
    path = safe_relative_file(root, value["path"], label=f"{label}.path")
    actual = sha256_file(path)
    if actual != value["sha256"]:
        raise ContractError(f"{label}: SHA-256 mismatch")
    return path
