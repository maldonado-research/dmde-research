#!/usr/bin/env python3
"""DMDE v0.9.20 strict raw-evidence ZIP validator.

This module uses the Python standard library plus NumPy.  It validates the
archive container, canonical manifest, byte/hash coverage, frozen-source
linkage, bridge linkage, backend/run identity, and a small set of evidence
semantics.  It does *not* replace the v0.9.20 spectral-bridge or BBN-physics
validators.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import ntpath
import os
import re
import stat
import struct
import sys
import tempfile
import unicodedata
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import numpy as np


SCHEMA_VERSION = "DMDE-RAW-EVIDENCE-CONTRACT-v0.9.20"
SOURCE_IDENTITY_SCHEMA = "DMDE-SOURCE-IDENTITY-v0.9.20"
OPERATOR_RECEIPT_SCHEMA = "DMDE-OPERATOR-PROBE-RECEIPT-v0.9.20"
WEAK_RATE_CLOSURE_SCHEMA = "DMDE-WEAK-RATE-CAUSAL-CLOSURE-v0.9.20"
BBN_CANARY_SCHEMA = "DMDE-BBN-CONSUMPTION-CANARY-v0.9.20"
STEPPER_STATE_HASH_DEFINITION = (
    "sha256(int64_le_time_index || six_C_order_float64_le_initial_state_rows_"
    "in_nue_nuebar_numu_numubar_nutau_nutaubar_order)"
)
MANIFEST_NAME = "DMDE_RAW_EVIDENCE_MANIFEST.csv"
CONTRACT_NAME = "DMDE_RAW_EVIDENCE_CONTRACT.json"
MANIFEST_COLUMNS = ["path", "role", "bytes", "sha256"]

LOCKED_SOURCE_HASHES = {
    "DMDE-SPEC-V099-4Q7N": "f5f9ad03206572f12103655714cf5c814287ba07dd45bdc3c6185312a3553dcb",
    "DMDE-SPEC-V099-8M2K": "ad86c5d4161afd12dde76e83bb19c9b313197fc31703baaf00cad7ba9f478c3e",
}

REQUIRED_ROLE_PATHS = {
    "contract": CONTRACT_NAME,
    "source_identity": "evidence/source_identity.json",
    "backend_identity": "evidence/backend_identity.json",
    "solver_config": "evidence/solver_config.json",
    "environment_lock": "evidence/environment.lock",
    "invocation": "evidence/invocation.txt",
    "stdout_log": "logs/stdout.log",
    "stderr_log": "logs/stderr.log",
    "bridge_history": "bridge/history.npz",
    "bridge_metadata": "bridge/metadata.json",
    "backend_code_artifact": "backend/code_artifact.bin",
    "operator_probe_receipt": "evidence/operator_probe_receipt.json",
    "weak_rate_closure_metadata": "evidence/weak_rate_closure_metadata.json",
    "weak_rates": "evidence/weak_rates.csv",
    "bbn_rate_input": "bbn/rate_input.csv",
    "bbn_code_artifact": "bbn/code_artifact.bin",
    "bbn_config": "bbn/config.json",
    "bbn_canary_contract": "DMDE_v0920_BBN_CANARY.json",
    "bbn_canary_baseline_input": "bbn_canary/replays/baseline_rate_input.csv",
    "bbn_canary_baseline_output": "bbn_canary/replays/baseline_output.json",
    "bbn_canary_summary": "bbn_canary/replays/canary_summary.csv",
    "bbn_canary_np_1pct": "bbn_canary/replays/np_plus_1pct_rate_input.csv",
    "bbn_canary_np_1pct_output": "bbn_canary/replays/np_plus_1pct_output.json",
    "bbn_canary_np_0p5pct": "bbn_canary/replays/np_plus_0p5pct_rate_input.csv",
    "bbn_canary_np_0p5pct_output": "bbn_canary/replays/np_plus_0p5pct_output.json",
    "bbn_canary_pn_1pct": "bbn_canary/replays/pn_plus_1pct_rate_input.csv",
    "bbn_canary_pn_1pct_output": "bbn_canary/replays/pn_plus_1pct_output.json",
    "bbn_canary_pn_0p5pct": "bbn_canary/replays/pn_plus_0p5pct_rate_input.csv",
    "bbn_canary_pn_0p5pct_output": "bbn_canary/replays/pn_plus_0p5pct_output.json",
    "bbn_abundance_history": "bbn/abundance_history.csv",
    "final_outputs": "evidence/final_outputs.json",
}

# Fixed ceilings are part of this versioned conformance contract.  Raising one
# is a contract change, not a provider-controlled option.
MAX_ARCHIVE_BYTES = 1_100 * 1024 * 1024
MAX_MEMBERS = 256
MAX_MEMBER_BYTES = 512 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
MAX_TOTAL_COMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250.0
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_TEXT_EVIDENCE_BYTES = 64 * 1024 * 1024
ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}

SHA256_RE = re.compile(r"[0-9a-f]{64}")
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
ROLE_RE = re.compile(r"(?:supplemental_[a-z0-9_]+|[a-z][a-z0-9_]*)")
PLACEHOLDERS = {
    "",
    "na",
    "n/a",
    "none",
    "null",
    "unknown",
    "tbd",
    "todo",
    "pending",
    "placeholder",
    "-",
    "?",
}

# Do not reject a bare substring such as "test" (for example, "latest" or a
# pytest package in an environment lock).  These patterns target explicit
# evidence/run labels.  JSON keys are not scanned because the v0.9.16 bridge
# legitimately has a key named production_or_synthetic; its *value* is checked.
PROHIBITED_PRODUCTION_PATTERNS = [
    re.compile(rb"(?i)(?<![a-z0-9])(synthetic|mocked?|dummy|fake|placeholder|fixture|fabricated)(?![a-z0-9])"),
    re.compile(rb"(?i)(?<![a-z0-9])test[-_ ]?(only|run|data|fixture)(?![a-z0-9])"),
    re.compile(rb"(?i)(?<![a-z0-9])dry[-_ ]?run(?![a-z0-9])"),
    re.compile(rb"(?i)(?<![a-z0-9])example[-_ ]?(only|data|output)(?![a-z0-9])"),
]

TEXT_ROLES = {
    "source_identity",
    "backend_identity",
    "solver_config",
    "environment_lock",
    "invocation",
    "stdout_log",
    "stderr_log",
    "bridge_metadata",
    "operator_probe_receipt",
    "weak_rate_closure_metadata",
    "weak_rates",
    "bbn_rate_input",
    "bbn_config",
    "bbn_canary_contract",
    "bbn_canary_baseline_input",
    "bbn_canary_baseline_output",
    "bbn_canary_summary",
    "bbn_canary_np_1pct",
    "bbn_canary_np_1pct_output",
    "bbn_canary_np_0p5pct",
    "bbn_canary_np_0p5pct_output",
    "bbn_canary_pn_1pct",
    "bbn_canary_pn_1pct_output",
    "bbn_canary_pn_0p5pct",
    "bbn_canary_pn_0p5pct_output",
    "bbn_abundance_history",
    "final_outputs",
    "contract",
}
JSON_ROLES = {
    "contract",
    "source_identity",
    "backend_identity",
    "solver_config",
    "bridge_metadata",
    "operator_probe_receipt",
    "weak_rate_closure_metadata",
    "bbn_config",
    "bbn_canary_contract",
    "bbn_canary_baseline_output",
    "bbn_canary_np_1pct_output",
    "bbn_canary_np_0p5pct_output",
    "bbn_canary_pn_1pct_output",
    "bbn_canary_pn_0p5pct_output",
    "final_outputs",
}

# These fields are permitted to differ between the locked coarse/fine pair.
# Every other solver_config member is conservatively treated as controlled
# physics/configuration and is included in the deterministic fingerprint.
GRID_VARIANT_SOLVER_FIELDS = {
    "momentum_bins",
    "run_role",
    "momentum_grid_description",
    # This nested object is run-result/control evidence, not configuration.
    # Its backend identity is already locked above and its observables are
    # validated independently, so grid-level result drift must not alter the
    # controlled-configuration fingerprint.
    "standard_model_control",
}


class ContractError(ValueError):
    """Raised for a safe-path or programmatic contract violation."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _nonplaceholder(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _json_no_duplicates(data: bytes, label: str) -> Any:
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON key {key!r}")
            out[key] = value
        return out

    try:
        text = data.decode("utf-8-sig")
        return json.loads(
            text,
            object_pairs_hook=hook,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"non-finite JSON constant {token}")),
        )
    except Exception as exc:
        raise ContractError(f"{label}: invalid JSON: {exc}") from exc


def _exact_keys(obj: Any, keys: Iterable[str], label: str, errors: list[str]) -> bool:
    wanted = set(keys)
    if not isinstance(obj, dict):
        errors.append(f"{label}: must be a JSON object")
        return False
    actual = set(obj)
    missing = sorted(wanted - actual)
    extra = sorted(actual - wanted)
    if missing:
        errors.append(f"{label}: missing keys: {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected keys: {', '.join(extra)}")
    return not missing and not extra


def _parse_utc(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        errors.append(f"{label}: must be an ISO-8601 UTC timestamp with seconds")
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError:
        errors.append(f"{label}: invalid calendar timestamp")
        return None


def _safe_member_name(name: str) -> str | None:
    """Return an error for a non-canonical archive path, else None."""
    if not name or "\x00" in name:
        return "empty or NUL-containing member path"
    if len(name.encode("utf-8")) > 512:
        return "member path exceeds 512 UTF-8 bytes"
    if name != unicodedata.normalize("NFC", name):
        return "member path is not Unicode NFC"
    if "\\" in name:
        return "backslashes are prohibited in member paths"
    if name.startswith("/") or PurePosixPath(name).is_absolute():
        return "absolute member path is prohibited"
    if ntpath.splitdrive(name)[0] or re.match(r"^[A-Za-z]:", name):
        return "drive-qualified member path is prohibited"
    segments = name.split("/")
    if any(part in {"", ".", ".."} for part in segments):
        return "member path contains empty, '.' or '..' segment"
    if any(len(part.encode("utf-8")) > 255 for part in segments):
        return "member path segment exceeds 255 UTF-8 bytes"
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        return "member path contains a control character"
    if name != name.strip():
        return "member path has leading/trailing whitespace"
    return None


def _member_kind(info: zipfile.ZipInfo) -> str:
    mode = (info.external_attr >> 16) & 0xFFFF
    ftype = stat.S_IFMT(mode)
    if info.is_dir() or info.filename.endswith("/") or ftype == stat.S_IFDIR:
        return "directory"
    if ftype == stat.S_IFLNK:
        return "symlink"
    # Creator systems often leave the Unix type unset.  Accept zero or a
    # regular file, reject devices/FIFOs/sockets and other special entries.
    if ftype not in {0, stat.S_IFREG}:
        return "special"
    return "file"


def safe_resolve_external(base: Path | str, supplied: str, *, require_file: bool = True) -> Path:
    """Resolve an untrusted external reference beneath a trusted base.

    Absolute paths, traversal, backslashes, symlinks in any supplied component,
    and escapes after resolution are rejected.  This closes the simple
    ``base / user_value`` weakness present in the v0.9.16 helper.
    """
    base_path = Path(base).resolve(strict=True)
    if not base_path.is_dir():
        raise ContractError("external base is not a directory")
    if not isinstance(supplied, str) or not supplied or "\x00" in supplied or "\\" in supplied:
        raise ContractError("external path must be a nonempty POSIX-style relative path")
    posix = PurePosixPath(supplied)
    if posix.is_absolute() or ntpath.splitdrive(supplied)[0] or any(p in {"", ".", ".."} for p in supplied.split("/")):
        raise ContractError("external path must be relative without '.', '..', drive, or empty segments")
    current = base_path
    for part in posix.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ContractError(f"external path traverses symlink: {part}")
        except OSError as exc:
            raise ContractError(f"external path lstat failure: {exc}") from exc
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"external path does not resolve: {exc}") from exc
    try:
        common = os.path.commonpath([str(base_path), str(resolved)])
    except ValueError as exc:
        raise ContractError("external path is on a different drive") from exc
    if common != str(base_path):
        raise ContractError("external path escapes trusted base")
    if require_file and (not resolved.is_file() or resolved.is_symlink()):
        raise ContractError("external path is not a regular non-symlink file")
    return resolved


def _parse_manifest(data: bytes, all_paths: set[str], errors: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if len(data) > MAX_MANIFEST_BYTES:
        errors.append("manifest exceeds fixed byte ceiling")
        return {}, {}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"manifest is not strict UTF-8: {exc}")
        return {}, {}
    if text.startswith("\ufeff"):
        errors.append("manifest must not contain a UTF-8 BOM")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != MANIFEST_COLUMNS:
            errors.append(f"manifest header must be exactly {','.join(MANIFEST_COLUMNS)}")
            return {}, {}
        rows = list(reader)
    except csv.Error as exc:
        errors.append(f"manifest CSV parse failure: {exc}")
        return {}, {}
    by_path: dict[str, dict[str, Any]] = {}
    by_role: dict[str, dict[str, Any]] = {}
    listed_order: list[str] = []
    for index, row in enumerate(rows, start=2):
        if None in row or any(row.get(k) is None for k in MANIFEST_COLUMNS):
            errors.append(f"manifest row {index}: wrong field count")
            continue
        path = row["path"]
        role = row["role"]
        byte_text = row["bytes"]
        digest = row["sha256"]
        listed_order.append(path)
        path_error = _safe_member_name(path)
        if path_error:
            errors.append(f"manifest row {index} path: {path_error}")
        if path == MANIFEST_NAME:
            errors.append(f"manifest row {index}: manifest must not list itself")
        if path in by_path:
            errors.append(f"manifest row {index}: duplicate path {path!r}")
        if not ROLE_RE.fullmatch(role):
            errors.append(f"manifest row {index}: invalid role {role!r}")
        if role in by_role:
            errors.append(f"manifest row {index}: duplicate role {role!r}")
        try:
            byte_count = int(byte_text)
            if byte_count < 0 or str(byte_count) != byte_text:
                raise ValueError
        except ValueError:
            errors.append(f"manifest row {index}: bytes must be canonical nonnegative decimal")
            byte_count = -1
        if not SHA256_RE.fullmatch(digest):
            errors.append(f"manifest row {index}: sha256 must be lowercase hexadecimal")
        normalized = {"path": path, "role": role, "bytes": byte_count, "sha256": digest}
        by_path[path] = normalized
        by_role[role] = normalized
    if listed_order != sorted(listed_order):
        errors.append("manifest rows must be sorted by path")
    expected_paths = all_paths - {MANIFEST_NAME}
    missing = sorted(expected_paths - set(by_path))
    extra = sorted(set(by_path) - expected_paths)
    if missing:
        errors.append("manifest omits archive members: " + ", ".join(missing))
    if extra:
        errors.append("manifest lists absent members: " + ", ".join(extra))
    for role, path in REQUIRED_ROLE_PATHS.items():
        row = by_role.get(role)
        if row is None:
            errors.append(f"manifest missing required role: {role}")
        elif row["path"] != path:
            errors.append(f"role {role} must use fixed path {path!r}")
    return by_path, by_role


def _prohibited_bytes(data: bytes) -> str | None:
    for pattern in PROHIBITED_PRODUCTION_PATTERNS:
        match = pattern.search(data)
        if match:
            return match.group(0).decode("ascii", "replace")
    return None


def _iter_json_leaf_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _iter_json_leaf_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_leaf_strings(child)


def _check_json_markers(value: Any, label: str, errors: list[str]) -> None:
    for item in _iter_json_leaf_strings(value):
        marker = _prohibited_bytes(item.encode("utf-8", "ignore"))
        if marker:
            errors.append(f"{label}: prohibited production marker {marker!r}")
            return


def _ref(contract_section: dict[str, Any], prefix: str) -> tuple[Any, Any]:
    return contract_section.get(prefix + "_path"), contract_section.get(prefix + "_sha256")


def _validate_ref(
    label: str,
    path_value: Any,
    hash_value: Any,
    role: str,
    by_role: dict[str, dict[str, Any]],
    actual: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    required_path = REQUIRED_ROLE_PATHS[role]
    if path_value != required_path:
        errors.append(f"{label}: path must be {required_path!r}")
    if not _is_sha256(hash_value):
        errors.append(f"{label}: sha256 must be lowercase hexadecimal")
    row = by_role.get(role)
    if row and row.get("path") == path_value:
        if row.get("sha256") != hash_value:
            errors.append(f"{label}: contract hash disagrees with manifest")
    info = actual.get(required_path)
    if info and _is_sha256(hash_value) and info.get("sha256") != hash_value:
        errors.append(f"{label}: contract hash disagrees with archive bytes")


def _decode_text(role: str, contents: dict[str, bytes], errors: list[str]) -> str | None:
    path = REQUIRED_ROLE_PATHS[role]
    data = contents.get(path)
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{path}: required text evidence is not UTF-8: {exc}")
        return None


def _validate_weak_rates(text: str | None, errors: list[str]) -> None:
    if text is None:
        return
    expected = ["time_s", "lambda_n_to_p_s_inv", "lambda_p_to_n_s_inv"]
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != expected:
            errors.append("weak_rates: header mismatch")
            return
        rows = list(reader)
    except csv.Error as exc:
        errors.append(f"weak_rates: CSV parse failure: {exc}")
        return
    if len(rows) < 2:
        errors.append("weak_rates: at least two history rows required")
        return
    previous = -math.inf
    for index, row in enumerate(rows, start=2):
        if None in row or any(row.get(key) is None for key in expected):
            errors.append(f"weak_rates row {index}: wrong field count")
            continue
        try:
            t = float(row[expected[0]])
            a = float(row[expected[1]])
            b = float(row[expected[2]])
        except (TypeError, ValueError, KeyError):
            errors.append(f"weak_rates row {index}: nonnumeric value")
            continue
        if not all(math.isfinite(x) for x in (t, a, b)) or t < 0 or t <= previous or a <= 0 or b < 0:
            errors.append(
                f"weak_rates row {index}: time must be finite, nonnegative, and strictly increase; "
                "n-to-p must be finite positive and p-to-n finite nonnegative"
            )
        previous = t


def _validate_bbn_rate_input(text: str | None, errors: list[str]) -> None:
    if text is None:
        return
    expected = [
        "time_s", "T_gamma_MeV", "H_s_inv",
        "lambda_n_to_p_s_inv", "lambda_p_to_n_s_inv",
    ]
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != expected:
            errors.append("bbn_rate_input: header mismatch")
            return
        rows = list(reader)
    except csv.Error as exc:
        errors.append(f"bbn_rate_input: CSV parse failure: {exc}")
        return
    if len(rows) < 2:
        errors.append("bbn_rate_input: at least two history rows required")
        return
    previous = -math.inf
    for index, row in enumerate(rows, start=2):
        if None in row or any(row.get(key) is None for key in expected):
            errors.append(f"bbn_rate_input row {index}: wrong field count")
            continue
        try:
            t, temperature, hubble, rate_np, rate_pn = (
                float(row[key]) for key in expected
            )
        except (TypeError, ValueError, KeyError):
            errors.append(f"bbn_rate_input row {index}: nonnumeric value")
            continue
        if (
            not all(math.isfinite(x) for x in (t, temperature, hubble, rate_np, rate_pn))
            or t < 0
            or t <= previous
            or temperature <= 0
            or hubble <= 0
            or rate_np <= 0
            or rate_pn < 0
        ):
            errors.append(
                f"bbn_rate_input row {index}: time must be finite, nonnegative, and strictly increase; "
                "temperature, H, and n-to-p must be finite positive; p-to-n must be finite nonnegative"
            )
        previous = t


def _validate_bbn_abundance_history(
    text: str | None,
    final_outputs: Any,
    errors: list[str],
) -> None:
    if text is None:
        return
    expected = ["time_s", "Yp_mass_fraction", "DH_x1e5"]
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames != expected:
            errors.append("bbn_abundance_history: header mismatch")
            return
        rows = list(reader)
    except csv.Error as exc:
        errors.append(f"bbn_abundance_history: CSV parse failure: {exc}")
        return
    if len(rows) < 2:
        errors.append("bbn_abundance_history: at least two history rows required")
        return
    previous = -math.inf
    parsed: list[tuple[float, float, float]] = []
    for index, row in enumerate(rows, start=2):
        if None in row or any(row.get(key) is None for key in expected):
            errors.append(f"bbn_abundance_history row {index}: wrong field count")
            continue
        try:
            t, yp, dh = (float(row[key]) for key in expected)
        except (TypeError, ValueError, KeyError):
            errors.append(f"bbn_abundance_history row {index}: nonnumeric value")
            continue
        if (
            not all(math.isfinite(x) for x in (t, yp, dh))
            or t < 0
            or t <= previous
            or yp < 0
            or dh < 0
        ):
            errors.append(
                f"bbn_abundance_history row {index}: time must be finite, nonnegative, and strictly "
                "increase; abundances must be finite nonnegative"
            )
        previous = t
        parsed.append((t, yp, dh))
    if parsed and isinstance(final_outputs, dict):
        try:
            final_yp = float(final_outputs["Yp_model"])
            final_dh = float(final_outputs["DH_x1e5_model"])
            if not math.isclose(parsed[-1][1], final_yp, rel_tol=0.0, abs_tol=1e-14):
                errors.append("bbn_abundance_history: final Yp disagrees with final_outputs")
            if not math.isclose(parsed[-1][2], final_dh, rel_tol=0.0, abs_tol=1e-14):
                errors.append("bbn_abundance_history: final D/H disagrees with final_outputs")
        except (KeyError, TypeError, ValueError):
            errors.append("bbn_abundance_history: final_outputs linkage failure")


def _validate_final_outputs(value: Any, blind_id: str, source_hash: str, errors: list[str]) -> None:
    required = {"blind_id", "source_payload_sha256", "Yp_model", "DH_x1e5_model", "Neff_CMB_model"}
    if not isinstance(value, dict) or not required.issubset(value):
        errors.append("final_outputs: missing required identity/result fields")
        return
    if value.get("blind_id") != blind_id or value.get("source_payload_sha256") != source_hash:
        errors.append("final_outputs: frozen-source identity mismatch")
    try:
        yp = float(value["Yp_model"])
        dh = float(value["DH_x1e5_model"])
        neff = float(value["Neff_CMB_model"])
    except (TypeError, ValueError):
        errors.append("final_outputs: result fields must be numeric")
        return
    if not (math.isfinite(yp) and 0 < yp < 1 and math.isfinite(dh) and 0.01 < dh < 20 and math.isfinite(neff) and 0 < neff < 20):
        errors.append("final_outputs: broad physical-range gate failed")


def _controlled_configuration_fingerprint(
    backend: dict[str, Any],
    backend_identity: dict[str, Any],
    solver_config: dict[str, Any],
    bbn_code_sha256: str,
    bbn_config_sha256: str,
) -> str:
    """Hash backend identity plus every non-grid solver configuration field."""
    material = {
        "fingerprint_schema": "DMDE-CONTROLLED-CONFIGURATION-v0.9.20",
        "backend": {
            "family": backend.get("family"),
            "name": backend.get("name"),
            "version_or_commit": backend.get("version_or_commit"),
            "code_artifact_sha256": backend.get("code_artifact_sha256"),
            "environment_sha256": backend.get("environment_sha256"),
        },
        "solver_config_non_grid": {
            key: solver_config[key]
            for key in sorted(solver_config)
            if key not in GRID_VARIANT_SOLVER_FIELDS
        },
        "bbn_consumption_path": {
            "code_artifact_sha256": bbn_code_sha256,
            "config_sha256": bbn_config_sha256,
            "temperature_window_MeV_inclusive": [0.5, 1.2],
            "perturbation_fractions": [0.01, 0.005],
        },
    }
    canonical = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(canonical)


def _validate_expected(contract: dict[str, Any], expected: dict[str, Any] | None, errors: list[str]) -> None:
    if expected is None:
        return
    if not isinstance(expected, dict):
        errors.append("expected context must be a JSON object")
        return
    mapping = {
        "blind_id": contract.get("blind_id"),
        "source_payload_sha256": contract.get("source_payload_sha256"),
        "bridge_history_sha256": contract.get("bridge", {}).get("history_sha256") if isinstance(contract.get("bridge"), dict) else None,
        "bridge_metadata_sha256": contract.get("bridge", {}).get("metadata_sha256") if isinstance(contract.get("bridge"), dict) else None,
        "backend_name": contract.get("backend", {}).get("name") if isinstance(contract.get("backend"), dict) else None,
        "backend_family": contract.get("backend", {}).get("family") if isinstance(contract.get("backend"), dict) else None,
        "backend_version_or_commit": contract.get("backend", {}).get("version_or_commit") if isinstance(contract.get("backend"), dict) else None,
        "run_class": contract.get("run", {}).get("class") if isinstance(contract.get("run"), dict) else None,
        "run_role": contract.get("run", {}).get("role") if isinstance(contract.get("run"), dict) else None,
    }
    unknown = sorted(set(expected) - set(mapping))
    if unknown:
        errors.append("expected context has unsupported keys: " + ", ".join(unknown))
    for key, wanted in expected.items():
        if key in mapping and mapping[key] != wanted:
            errors.append(f"expected context mismatch: {key}")


def _validate_contract(
    contract: Any,
    by_role: dict[str, dict[str, Any]],
    actual: dict[str, dict[str, Any]],
    contents: dict[str, bytes],
    *,
    require_production: bool,
    expected: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    top_keys = {"schema_version", "blind_id", "source_payload_sha256", "bridge", "backend", "run", "evidence"}
    if not _exact_keys(contract, top_keys, "contract", errors):
        return metrics
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append("contract schema_version mismatch")
    blind_id = contract.get("blind_id")
    source_hash = contract.get("source_payload_sha256")
    if blind_id not in LOCKED_SOURCE_HASHES:
        errors.append("contract blind_id is not one of the two frozen cards")
    elif source_hash != LOCKED_SOURCE_HASHES[blind_id]:
        errors.append("contract source_payload_sha256 does not match frozen blind card")
    if not _is_sha256(source_hash):
        errors.append("contract source_payload_sha256 must be lowercase hexadecimal")
    metrics.update({"blind_id": blind_id, "source_payload_sha256": source_hash})

    bridge = contract.get("bridge")
    if _exact_keys(bridge, {"history_path", "history_sha256", "metadata_path", "metadata_sha256"}, "contract.bridge", errors):
        _validate_ref("bridge history", bridge["history_path"], bridge["history_sha256"], "bridge_history", by_role, actual, errors)
        _validate_ref("bridge metadata", bridge["metadata_path"], bridge["metadata_sha256"], "bridge_metadata", by_role, actual, errors)
        metrics.update({"bridge_history_sha256": bridge.get("history_sha256"), "bridge_metadata_sha256": bridge.get("metadata_sha256")})

    backend = contract.get("backend")
    backend_keys = {
        "family", "name", "version_or_commit",
        "identity_path", "identity_sha256",
        "environment_path", "environment_sha256",
        "code_artifact_path", "code_artifact_sha256",
    }
    if _exact_keys(backend, backend_keys, "contract.backend", errors):
        for key in ("family", "name", "version_or_commit"):
            if not _nonplaceholder(backend.get(key)):
                errors.append(f"contract.backend.{key}: blank or placeholder")
        _validate_ref("backend identity", backend["identity_path"], backend["identity_sha256"], "backend_identity", by_role, actual, errors)
        _validate_ref("backend environment", backend["environment_path"], backend["environment_sha256"], "environment_lock", by_role, actual, errors)
        _validate_ref(
            "backend code artifact",
            backend["code_artifact_path"],
            backend["code_artifact_sha256"],
            "backend_code_artifact",
            by_role,
            actual,
            errors,
        )
        code_artifact_info = actual.get(REQUIRED_ROLE_PATHS["backend_code_artifact"])
        if code_artifact_info is not None and code_artifact_info.get("bytes", 0) <= 0:
            errors.append("backend code artifact must be nonempty")
        metrics.update(
            {
                "backend_family": backend.get("family"),
                "backend_name": backend.get("name"),
                "backend_version_or_commit": backend.get("version_or_commit"),
                "backend_code_artifact_sha256": backend.get("code_artifact_sha256"),
                "backend_environment_sha256": backend.get("environment_sha256"),
            }
        )

    run = contract.get("run")
    run_keys = {
        "class",
        "role",
        "started_utc",
        "completed_utc",
        "exit_code",
        "invocation_path",
        "invocation_sha256",
        "stdout_path",
        "stdout_sha256",
        "stderr_path",
        "stderr_sha256",
    }
    run_class = None
    if _exact_keys(run, run_keys, "contract.run", errors):
        run_class = run.get("class")
        run_role = run.get("role")
        if run_class not in {"production", "conformance"}:
            errors.append("contract.run.class must be production or conformance")
        if require_production and run_class != "production":
            errors.append("production validation rejects non-production run class")
        if run_role not in {"coarse", "fine"}:
            errors.append("contract.run.role must be coarse or fine")
        started = _parse_utc(run.get("started_utc"), "contract.run.started_utc", errors)
        completed = _parse_utc(run.get("completed_utc"), "contract.run.completed_utc", errors)
        if started and completed and completed < started:
            errors.append("contract.run.completed_utc precedes started_utc")
        if type(run.get("exit_code")) is not int or run.get("exit_code") != 0:
            errors.append("contract.run.exit_code must be integer zero")
        _validate_ref("run invocation", run["invocation_path"], run["invocation_sha256"], "invocation", by_role, actual, errors)
        _validate_ref("run stdout", run["stdout_path"], run["stdout_sha256"], "stdout_log", by_role, actual, errors)
        _validate_ref("run stderr", run["stderr_path"], run["stderr_sha256"], "stderr_log", by_role, actual, errors)
        metrics["run_class"] = run_class
        metrics["run_role"] = run_role
        metrics["started_utc"] = run.get("started_utc")
        metrics["completed_utc"] = run.get("completed_utc")

    evidence = contract.get("evidence")
    evidence_keys = {
        "source_identity", "solver_config", "operator_probe_receipt",
        "weak_rate_closure_metadata", "weak_rates", "bbn_rate_input",
        "bbn_code_artifact", "bbn_config", "bbn_canary_contract",
        "bbn_canary_baseline_input", "bbn_canary_baseline_output",
        "bbn_canary_summary", "bbn_canary_np_1pct",
        "bbn_canary_np_1pct_output", "bbn_canary_np_0p5pct",
        "bbn_canary_np_0p5pct_output", "bbn_canary_pn_1pct",
        "bbn_canary_pn_1pct_output", "bbn_canary_pn_0p5pct",
        "bbn_canary_pn_0p5pct_output", "bbn_abundance_history", "final_outputs",
    }
    if _exact_keys(evidence, evidence_keys, "contract.evidence", errors):
        for key, role in (
            ("source_identity", "source_identity"),
            ("solver_config", "solver_config"),
            ("operator_probe_receipt", "operator_probe_receipt"),
            ("weak_rate_closure_metadata", "weak_rate_closure_metadata"),
            ("weak_rates", "weak_rates"),
            ("bbn_rate_input", "bbn_rate_input"),
            ("bbn_code_artifact", "bbn_code_artifact"),
            ("bbn_config", "bbn_config"),
            ("bbn_canary_contract", "bbn_canary_contract"),
            ("bbn_canary_baseline_input", "bbn_canary_baseline_input"),
            ("bbn_canary_baseline_output", "bbn_canary_baseline_output"),
            ("bbn_canary_summary", "bbn_canary_summary"),
            ("bbn_canary_np_1pct", "bbn_canary_np_1pct"),
            ("bbn_canary_np_1pct_output", "bbn_canary_np_1pct_output"),
            ("bbn_canary_np_0p5pct", "bbn_canary_np_0p5pct"),
            ("bbn_canary_np_0p5pct_output", "bbn_canary_np_0p5pct_output"),
            ("bbn_canary_pn_1pct", "bbn_canary_pn_1pct"),
            ("bbn_canary_pn_1pct_output", "bbn_canary_pn_1pct_output"),
            ("bbn_canary_pn_0p5pct", "bbn_canary_pn_0p5pct"),
            ("bbn_canary_pn_0p5pct_output", "bbn_canary_pn_0p5pct_output"),
            ("bbn_abundance_history", "bbn_abundance_history"),
            ("final_outputs", "final_outputs"),
        ):
            ref = evidence.get(key)
            if _exact_keys(ref, {"path", "sha256"}, f"contract.evidence.{key}", errors):
                _validate_ref(key, ref["path"], ref["sha256"], role, by_role, actual, errors)

    # Parse and cross-link the required structured evidence.
    structured: dict[str, Any] = {}
    for role in (
        "source_identity", "backend_identity", "solver_config", "bridge_metadata",
        "operator_probe_receipt", "weak_rate_closure_metadata",
        "bbn_config", "bbn_canary_contract", "final_outputs",
    ):
        path = REQUIRED_ROLE_PATHS[role]
        if path in contents:
            try:
                structured[role] = _json_no_duplicates(contents[path], path)
            except ContractError as exc:
                errors.append(str(exc))

    source_identity = structured.get("source_identity")
    if isinstance(source_identity, dict):
        if source_identity.get("schema_version") != SOURCE_IDENTITY_SCHEMA or source_identity.get("blind_id") != blind_id or source_identity.get("source_payload_sha256") != source_hash:
            errors.append("source_identity: frozen identity linkage mismatch")
    else:
        errors.append("source_identity: JSON object required")

    backend_identity = structured.get("backend_identity")
    if isinstance(backend_identity, dict) and isinstance(backend, dict):
        for key in ("family", "name", "version_or_commit"):
            if backend_identity.get(key) != backend.get(key):
                errors.append(f"backend_identity: {key} disagrees with contract")
        if not _is_sha256(backend_identity.get("code_artifact_sha256")):
            errors.append("backend_identity: code_artifact_sha256 missing or invalid")
        elif isinstance(backend, dict) and backend_identity.get("code_artifact_sha256") != backend.get("code_artifact_sha256"):
            errors.append("backend_identity: code_artifact_sha256 disagrees with contract/archive member")
    else:
        errors.append("backend_identity: JSON object required")

    solver = structured.get("solver_config")
    if isinstance(solver, dict):
        required_solver_keys = {
            "momentum_bins", "run_role", "momentum_grid_description",
            "spectral_source_treatment",
            "source_rhs_stage", "source_rhs_units", "source_rhs_export_method",
            "source_rhs_production_callable", "source_rhs_adapter",
            "source_rhs_impulse_test_command",
            "state_normalization_density_definition",
            "transport_stepper_production_callable", "transport_stepper_source_toggle",
            "operator_probe_command", "weak_rate_production_callable",
            "weak_rate_canonical_process_map",
            "weak_rate_born_sentinel_definition", "bbn_consumption_canary_command",
            "collision_treatment", "oscillation_treatment", "weak_rate_treatment",
            "background_to_bbn_bridge", "bbn_network", "nuclear_rate_set",
            "neutron_lifetime_s", "refinement_settings", "standard_model_control",
        }
        for key in sorted(required_solver_keys - set(solver)):
            errors.append(f"solver_config: missing {key}")
        for key in (
            "momentum_grid_description", "spectral_source_treatment",
            "source_rhs_stage", "source_rhs_units", "source_rhs_export_method",
            "source_rhs_production_callable", "source_rhs_adapter",
            "source_rhs_impulse_test_command",
            "state_normalization_density_definition",
            "transport_stepper_production_callable", "transport_stepper_source_toggle",
            "operator_probe_command", "weak_rate_production_callable",
            "weak_rate_canonical_process_map",
            "weak_rate_born_sentinel_definition", "bbn_consumption_canary_command",
            "collision_treatment", "oscillation_treatment",
            "weak_rate_treatment", "background_to_bbn_bridge", "bbn_network",
            "nuclear_rate_set", "refinement_settings",
        ):
            if key in solver and not _nonplaceholder(solver.get(key)):
                errors.append(f"solver_config: {key} must be a nonplaceholder string")
        if solver.get("source_rhs_stage") != "pre_collision_pre_oscillation":
            errors.append("solver_config: source_rhs_stage must be pre_collision_pre_oscillation")
        if solver.get("source_rhs_units") != "dY_per_dt_dq_s^-1":
            errors.append("solver_config: source_rhs_units must be dY_per_dt_dq_s^-1")
        mb = solver.get("momentum_bins")
        if isinstance(mb, bool) or not isinstance(mb, int) or mb < 21:
            errors.append("solver_config: momentum_bins must be integer >= 21")
        if isinstance(run, dict) and solver.get("run_role") != run.get("role"):
            errors.append("solver_config: run_role disagrees with contract")
        try:
            tau_n = float(solver.get("neutron_lifetime_s"))
            if not math.isfinite(tau_n) or not 800 < tau_n < 1000:
                raise ValueError
        except (TypeError, ValueError):
            errors.append("solver_config: neutron_lifetime_s broad-range failure")
        control = solver.get("standard_model_control")
        control_keys = {
            "backend_family", "backend_name", "backend_version_or_commit",
            "Yp", "DH_x1e5", "Neff_CMB", "convergence_pass",
        }
        if not _exact_keys(control, control_keys, "solver_config.standard_model_control", errors):
            pass
        elif control.get("convergence_pass") is not True:
            errors.append("solver_config: converged standard_model_control object required")
        else:
            if isinstance(backend, dict):
                for control_key, backend_key in (
                    ("backend_family", "family"),
                    ("backend_name", "name"),
                    ("backend_version_or_commit", "version_or_commit"),
                ):
                    if control.get(control_key) != backend.get(backend_key):
                        errors.append(
                            f"solver_config.standard_model_control: {control_key} disagrees with contract"
                        )
            try:
                if any(isinstance(control[key], bool) for key in ("Yp", "DH_x1e5", "Neff_CMB")):
                    raise ValueError
                cy = float(control["Yp"])
                cd = float(control["DH_x1e5"])
                cn = float(control["Neff_CMB"])
                if not (
                    all(math.isfinite(x) for x in (cy, cd, cn))
                    and 0.23 < cy < 0.27
                    and 2.0 < cd < 3.2
                    and 2.8 < cn < 3.2
                ):
                    raise ValueError
                metrics.update({
                    "standard_model_control_Yp": cy,
                    "standard_model_control_DH_x1e5": cd,
                    "standard_model_control_Neff_CMB": cn,
                })
            except (KeyError, TypeError, ValueError):
                errors.append("solver_config: standard_model_control broad-range failure")
        metrics.update(
            {
                "momentum_bins": solver.get("momentum_bins"),
                "momentum_grid_description": solver.get("momentum_grid_description"),
                "spectral_source_treatment": solver.get("spectral_source_treatment"),
                "source_rhs_stage": solver.get("source_rhs_stage"),
                "source_rhs_units": solver.get("source_rhs_units"),
                "source_rhs_export_method": solver.get("source_rhs_export_method"),
                "source_rhs_production_callable": solver.get("source_rhs_production_callable"),
                "source_rhs_adapter": solver.get("source_rhs_adapter"),
                "source_rhs_impulse_test_command": solver.get("source_rhs_impulse_test_command"),
                "state_normalization_density_definition": solver.get("state_normalization_density_definition"),
                "transport_stepper_production_callable": solver.get("transport_stepper_production_callable"),
                "transport_stepper_source_toggle": solver.get("transport_stepper_source_toggle"),
                "operator_probe_command": solver.get("operator_probe_command"),
                "weak_rate_production_callable": solver.get("weak_rate_production_callable"),
                "weak_rate_canonical_process_map": solver.get("weak_rate_canonical_process_map"),
                "weak_rate_born_sentinel_definition": solver.get("weak_rate_born_sentinel_definition"),
                "bbn_consumption_canary_command": solver.get("bbn_consumption_canary_command"),
                "collision_treatment": solver.get("collision_treatment"),
                "oscillation_treatment": solver.get("oscillation_treatment"),
                "weak_rate_treatment": solver.get("weak_rate_treatment"),
                "background_to_bbn_bridge": solver.get("background_to_bbn_bridge"),
                "bbn_network": solver.get("bbn_network"),
                "nuclear_rate_set": solver.get("nuclear_rate_set"),
            }
        )
        try:
            metrics["neutron_lifetime_s"] = float(solver.get("neutron_lifetime_s"))
        except (TypeError, ValueError):
            metrics["neutron_lifetime_s"] = solver.get("neutron_lifetime_s")
    else:
        errors.append("solver_config: JSON object required")

    bridge_metadata = structured.get("bridge_metadata")
    if isinstance(bridge_metadata, dict):
        if bridge_metadata.get("blind_id") != blind_id or bridge_metadata.get("source_payload_sha256") != source_hash:
            errors.append("bridge_metadata: frozen identity linkage mismatch")
        if require_production and bridge_metadata.get("production_or_synthetic") != "production":
            errors.append("bridge_metadata: production_or_synthetic must equal production")
        if isinstance(backend, dict):
            if bridge_metadata.get("backend_family") != backend.get("family"):
                errors.append("bridge_metadata: backend_family disagrees with contract")
            if bridge_metadata.get("backend_name") != backend.get("name"):
                errors.append("bridge_metadata: backend_name disagrees with contract")
            if bridge_metadata.get("backend_version_or_commit") != backend.get("version_or_commit"):
                errors.append("bridge_metadata: backend version disagrees with contract")
        if isinstance(run, dict) and bridge_metadata.get("run_role") != run.get("role"):
            errors.append("bridge_metadata: run_role disagrees with contract")
        if isinstance(solver, dict):
            for key in (
                "momentum_grid_description",
                "spectral_source_treatment",
                "source_rhs_stage",
                "source_rhs_units",
                "source_rhs_export_method",
                "source_rhs_production_callable",
                "source_rhs_adapter",
                "source_rhs_impulse_test_command",
                "state_normalization_density_definition",
                "transport_stepper_production_callable",
                "transport_stepper_source_toggle",
                "operator_probe_command",
                "weak_rate_production_callable",
                "weak_rate_canonical_process_map",
                "weak_rate_born_sentinel_definition",
                "bbn_consumption_canary_command",
                "collision_treatment",
                "oscillation_treatment",
                "background_to_bbn_bridge",
                "nuclear_rate_set",
            ):
                if bridge_metadata.get(key) != solver.get(key):
                    errors.append(f"bridge_metadata: {key} disagrees with solver_config")
            try:
                bridge_tau_n = float(bridge_metadata.get("neutron_lifetime_s"))
                solver_tau_n = float(solver.get("neutron_lifetime_s"))
                if not (
                    math.isfinite(bridge_tau_n)
                    and math.isfinite(solver_tau_n)
                    and math.isclose(bridge_tau_n, solver_tau_n, rel_tol=0.0, abs_tol=1e-12)
                ):
                    raise ValueError
            except (TypeError, ValueError):
                errors.append("bridge_metadata: neutron_lifetime_s disagrees with solver_config")
    else:
        errors.append("bridge_metadata: JSON object required")

    operator_receipt = structured.get("operator_probe_receipt")
    operator_receipt_keys = {
        "schema_version", "blind_id", "source_payload_sha256",
        "bridge_history_sha256", "run_role", "production_stepper_callable",
        "source_toggle", "probe_command", "allowed_configuration_delta",
        "state_hash_definition", "state_hashes", "generated_utc",
    }
    if _exact_keys(operator_receipt, operator_receipt_keys, "operator_probe_receipt", errors):
        if operator_receipt.get("schema_version") != OPERATOR_RECEIPT_SCHEMA:
            errors.append("operator_probe_receipt: schema_version mismatch")
        if operator_receipt.get("blind_id") != blind_id or operator_receipt.get("source_payload_sha256") != source_hash:
            errors.append("operator_probe_receipt: frozen identity mismatch")
        if isinstance(bridge, dict) and operator_receipt.get("bridge_history_sha256") != bridge.get("history_sha256"):
            errors.append("operator_probe_receipt: bridge history hash mismatch")
        if isinstance(run, dict) and operator_receipt.get("run_role") != run.get("role"):
            errors.append("operator_probe_receipt: run role mismatch")
        if isinstance(solver, dict):
            for receipt_key, solver_key in (
                ("production_stepper_callable", "transport_stepper_production_callable"),
                ("source_toggle", "transport_stepper_source_toggle"),
                ("probe_command", "operator_probe_command"),
            ):
                if operator_receipt.get(receipt_key) != solver.get(solver_key):
                    errors.append(f"operator_probe_receipt: {receipt_key} disagrees with solver_config")
        if operator_receipt.get("allowed_configuration_delta") != "source_enabled:true->false_only":
            errors.append("operator_probe_receipt: allowed configuration delta mismatch")
        if operator_receipt.get("state_hash_definition") != STEPPER_STATE_HASH_DEFINITION:
            errors.append("operator_probe_receipt: state hash definition mismatch")
        state_hashes = operator_receipt.get("state_hashes")
        if not isinstance(state_hashes, list) or len(state_hashes) != 8 or any(not _is_sha256(value) for value in state_hashes):
            errors.append("operator_probe_receipt: exactly eight lowercase state hashes required")
        if _parse_utc(operator_receipt.get("generated_utc"), "operator_probe_receipt.generated_utc", errors) is None:
            pass
    else:
        errors.append("operator_probe_receipt: JSON object required")

    weak_metadata = structured.get("weak_rate_closure_metadata")
    weak_keys = {
        "schema_version", "bridge_history_sha256", "weak_rate_production_callable",
        "weak_rate_code_sha256", "weak_rate_config_sha256",
        "n_to_p_process_labels", "p_to_n_process_labels", "born_normalization",
        "electron_positron_distribution", "born_processes_checked",
        "born_blocking_convention", "born_process_relative_band",
        "born_direction_total_relative_band",
        "born_non_negligible_floor_relative_to_peak",
        "born_non_negligible_floor_absolute_s_inv", "late_decay_relative_tolerance",
        "late_temperature_max_MeV", "momentum_integrands_present",
        "integrand_sum_relative_tolerance", "integrand_sum_absolute_tolerance_s_inv",
    }
    if _exact_keys(weak_metadata, weak_keys, "weak_rate_closure_metadata", errors):
        if weak_metadata.get("schema_version") != WEAK_RATE_CLOSURE_SCHEMA:
            errors.append("weak_rate_closure_metadata: schema_version mismatch")
        if isinstance(bridge, dict) and weak_metadata.get("bridge_history_sha256") != bridge.get("history_sha256"):
            errors.append("weak_rate_closure_metadata: bridge history hash mismatch")
        if isinstance(backend, dict) and weak_metadata.get("weak_rate_code_sha256") != backend.get("code_artifact_sha256"):
            errors.append("weak_rate_closure_metadata: weak-rate code hash disagrees with backend artifact")
        solver_info = actual.get(REQUIRED_ROLE_PATHS["solver_config"])
        if solver_info and weak_metadata.get("weak_rate_config_sha256") != solver_info.get("sha256"):
            errors.append("weak_rate_closure_metadata: weak-rate config hash disagrees with solver_config bytes")
        if isinstance(solver, dict) and weak_metadata.get("weak_rate_production_callable") != solver.get("weak_rate_production_callable"):
            errors.append("weak_rate_closure_metadata: production callable disagrees with solver_config")
        if isinstance(bridge_metadata, dict):
            for key in ("n_to_p_process_labels", "p_to_n_process_labels"):
                if weak_metadata.get(key) != bridge_metadata.get(key):
                    errors.append(f"weak_rate_closure_metadata: {key} disagrees with bridge metadata")
    else:
        errors.append("weak_rate_closure_metadata: JSON object required")

    bbn_contract = structured.get("bbn_canary_contract")
    fixed_canary_refs = {
        ("code",): "bbn_code_artifact",
        ("config",): "bbn_config",
        ("production", "rate_input"): "bbn_rate_input",
        ("production", "output"): "final_outputs",
        ("baseline_replay", "rate_input"): "bbn_canary_baseline_input",
        ("baseline_replay", "output"): "bbn_canary_baseline_output",
        ("canary_summary",): "bbn_canary_summary",
    }
    run_roles = {
        "np_plus_1pct": ("bbn_canary_np_1pct", "bbn_canary_np_1pct_output"),
        "np_plus_0p5pct": ("bbn_canary_np_0p5pct", "bbn_canary_np_0p5pct_output"),
        "pn_plus_1pct": ("bbn_canary_pn_1pct", "bbn_canary_pn_1pct_output"),
        "pn_plus_0p5pct": ("bbn_canary_pn_0p5pct", "bbn_canary_pn_0p5pct_output"),
    }
    if isinstance(bbn_contract, dict):
        if bbn_contract.get("schema_version") != BBN_CANARY_SCHEMA:
            errors.append("bbn_canary_contract: schema_version mismatch")
        for chain, role in fixed_canary_refs.items():
            value: Any = bbn_contract
            try:
                for key in chain:
                    value = value[key]
            except (KeyError, TypeError):
                errors.append(f"bbn_canary_contract: missing {'.'.join(chain)} reference")
                continue
            if isinstance(value, dict):
                _validate_ref(f"bbn_canary_contract.{'.'.join(chain)}", value.get("path"), value.get("sha256"), role, by_role, actual, errors)
            else:
                errors.append(f"bbn_canary_contract.{'.'.join(chain)}: file reference object required")
        runs = bbn_contract.get("runs")
        if isinstance(runs, list):
            seen_run_ids: set[str] = set()
            for run_value in runs:
                if not isinstance(run_value, dict):
                    continue
                run_id = run_value.get("run_id")
                if run_id in run_roles and run_id not in seen_run_ids:
                    input_role, output_role = run_roles[run_id]
                    for key, role in (("rate_input", input_role), ("output", output_role)):
                        ref = run_value.get(key)
                        if isinstance(ref, dict):
                            _validate_ref(f"bbn_canary_contract.{run_id}.{key}", ref.get("path"), ref.get("sha256"), role, by_role, actual, errors)
                        else:
                            errors.append(f"bbn_canary_contract.{run_id}.{key}: file reference object required")
                    seen_run_ids.add(run_id)
            if seen_run_ids != set(run_roles):
                errors.append("bbn_canary_contract: canonical four-run reference set mismatch")
        else:
            errors.append("bbn_canary_contract: runs list required")
    else:
        errors.append("bbn_canary_contract: JSON object required")

    final_outputs = structured.get("final_outputs")
    _validate_final_outputs(final_outputs, blind_id, source_hash, errors)
    _validate_weak_rates(_decode_text("weak_rates", contents, errors), errors)
    _validate_bbn_rate_input(_decode_text("bbn_rate_input", contents, errors), errors)
    _validate_bbn_abundance_history(
        _decode_text("bbn_abundance_history", contents, errors),
        final_outputs,
        errors,
    )

    if isinstance(backend, dict) and isinstance(backend_identity, dict) and isinstance(solver, dict):
        try:
            bbn_code_info = actual.get(REQUIRED_ROLE_PATHS["bbn_code_artifact"], {})
            bbn_config_info = actual.get(REQUIRED_ROLE_PATHS["bbn_config"], {})
            bbn_code_sha256 = bbn_code_info.get("sha256", "")
            bbn_config_sha256 = bbn_config_info.get("sha256", "")
            if not _is_sha256(bbn_code_sha256) or not _is_sha256(bbn_config_sha256):
                raise ValueError("BBN code/config hashes unavailable")
            metrics["controlled_configuration_fingerprint"] = _controlled_configuration_fingerprint(
                backend, backend_identity, solver, bbn_code_sha256, bbn_config_sha256
            )
            metrics["bbn_code_artifact_sha256"] = bbn_code_sha256
            metrics["bbn_config_sha256"] = bbn_config_sha256
        except (TypeError, ValueError) as exc:
            errors.append(f"controlled configuration fingerprint failure: {exc}")

    for role in ("environment_lock", "invocation", "stdout_log", "stderr_log"):
        text = _decode_text(role, contents, errors)
        if role in {"environment_lock", "invocation", "stdout_log"} and text is not None and not text.strip():
            errors.append(f"{role}: must not be empty")

    if require_production and run_class == "production":
        # Paths/roles are evidence too; then inspect text bodies.  For JSON,
        # scan only leaf values so legitimate schema keys do not trip the gate.
        for row in by_role.values():
            marker = _prohibited_bytes((row["path"] + "\n" + row["role"]).encode("utf-8"))
            if marker:
                errors.append(f"manifest production marker {marker!r} in {row['path']!r}")
        path_roles = {row["path"]: role for role, row in by_role.items()}
        for member_path, member_result in actual.items():
            marker = member_result.get("production_marker")
            role = path_roles.get(member_path)
            # JSON keys may legitimately contain words such as
            # production_or_synthetic. JSON leaf values are scanned below.
            if marker and role in TEXT_ROLES and role not in JSON_ROLES:
                errors.append(f"member {member_path!r}: prohibited production marker {marker!r}")
        _check_json_markers(contract, "contract", errors)
        for role, value in structured.items():
            _check_json_markers(value, role, errors)

    _validate_expected(contract, expected, errors)
    return metrics


def validate_archive_file(
    archive_path: Path | str,
    *,
    require_production: bool = True,
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one already-safely-resolved raw-evidence archive."""
    path = Path(archive_path)
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}
    if path.suffix.lower() != ".zip":
        errors.append("raw evidence must have a .zip filename")
    try:
        size = path.stat().st_size
        if not path.is_file() or path.is_symlink():
            errors.append("raw evidence path must be a regular non-symlink file")
        if size > MAX_ARCHIVE_BYTES:
            errors.append("archive exceeds fixed container byte ceiling")
    except OSError as exc:
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": [f"archive stat failure: {exc}"], "warnings": [], "metrics": {}}
    try:
        with path.open("rb") as handle:
            signature = handle.read(4)
        if signature != b"PK\x03\x04" or not zipfile.is_zipfile(path):
            errors.append("raw evidence is not a real nonempty ZIP archive")
            return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}
    except OSError as exc:
        errors.append(f"archive read failure: {exc}")
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}

    # Require a single-disk, comment-free archive ending exactly at its EOCD.
    # This rejects appended covert bytes and self-extracting/polyglot layouts.
    try:
        with path.open("rb") as handle:
            seek_back = min(size, 65557)
            handle.seek(size - seek_back)
            tail = handle.read(seek_back)
        eocd_local = tail.rfind(b"PK\x05\x06")
        if eocd_local < 0 or len(tail) - eocd_local < 22:
            errors.append("ZIP end-of-central-directory record missing")
        else:
            eocd_offset = size - seek_back + eocd_local
            (_sig, disk_no, central_disk, disk_entries, total_entries, central_size, central_offset, comment_size) = struct.unpack_from("<4s4H2LH", tail, eocd_local)
            if disk_no != 0 or central_disk != 0 or disk_entries != total_entries:
                errors.append("multi-disk ZIP archives are prohibited")
            if comment_size != 0 or eocd_offset + 22 + comment_size != size:
                errors.append("ZIP comments or trailing bytes are prohibited")
            if central_offset + central_size != eocd_offset:
                errors.append("non-canonical central-directory placement")
    except (OSError, ValueError) as exc:
        errors.append(f"ZIP envelope parse failure: {exc}")
    if errors:
        return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}

    actual: dict[str, dict[str, Any]] = {}
    contents: dict[str, bytes] = {}
    by_path: dict[str, dict[str, Any]] = {}
    by_role: dict[str, dict[str, Any]] = {}
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if archive.comment:
                errors.append("ZIP archive comment is prohibited")
            metrics["member_count"] = len(infos)
            if not infos:
                errors.append("archive is empty")
            if len(infos) > MAX_MEMBERS:
                errors.append(f"archive has more than {MAX_MEMBERS} members")
            names: set[str] = set()
            folded: set[str] = set()
            total_uncompressed = 0
            total_compressed = 0
            with path.open("rb") as raw_container:
                for info in infos:
                    try:
                        raw_container.seek(info.header_offset)
                        local_header = raw_container.read(30)
                        if len(local_header) != 30 or local_header[:4] != b"PK\x03\x04":
                            errors.append(f"member {info.filename!r}: invalid local header")
                        else:
                            local_flags = int.from_bytes(local_header[6:8], "little")
                            local_compression = int.from_bytes(local_header[8:10], "little")
                            if local_flags & 0x1:
                                errors.append(f"member {info.filename!r}: local-header encryption is prohibited")
                            if local_compression != info.compress_type:
                                errors.append(f"member {info.filename!r}: local/central compression mismatch")
                    except OSError as exc:
                        errors.append(f"member {info.filename!r}: local-header read failure: {exc}")
                    name_error = _safe_member_name(info.filename)
                    if name_error:
                        errors.append(f"member {info.filename!r}: {name_error}")
                    folded_name = unicodedata.normalize("NFC", info.filename).casefold()
                    if info.filename in names:
                        errors.append(f"duplicate member path: {info.filename!r}")
                    if folded_name in folded:
                        errors.append(f"casefold/NFC member collision: {info.filename!r}")
                    names.add(info.filename)
                    folded.add(folded_name)
                    kind = _member_kind(info)
                    if kind != "file":
                        errors.append(f"member {info.filename!r}: {kind} entries are prohibited")
                    if info.flag_bits & 0x1 or info.compress_type == 99:
                        errors.append(f"member {info.filename!r}: encryption is prohibited")
                    if info.comment:
                        errors.append(f"member {info.filename!r}: per-member comments are prohibited")
                    if info.extra:
                        errors.append(f"member {info.filename!r}: ZIP extra fields are prohibited by the canonical contract")
                    if info.compress_type not in ALLOWED_COMPRESSION:
                        errors.append(f"member {info.filename!r}: unsupported compression method")
                    if info.file_size < 0 or info.file_size > MAX_MEMBER_BYTES:
                        errors.append(f"member {info.filename!r}: uncompressed size exceeds ceiling")
                    if info.compress_size < 0:
                        errors.append(f"member {info.filename!r}: negative compressed size")
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > MAX_COMPRESSION_RATIO:
                        errors.append(f"member {info.filename!r}: compression ratio {ratio:.3f} exceeds {MAX_COMPRESSION_RATIO:g}")
                    total_uncompressed += max(info.file_size, 0)
                    total_compressed += max(info.compress_size, 0)
            metrics.update({"total_uncompressed_bytes": total_uncompressed, "total_compressed_bytes": total_compressed})
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                errors.append("archive total uncompressed size exceeds ceiling")
            if total_compressed > MAX_TOTAL_COMPRESSED_BYTES:
                errors.append("archive total compressed size exceeds ceiling")
            manifest_candidates = [n for n in names if n == MANIFEST_NAME]
            other_manifest_csv = [n for n in names if n != MANIFEST_NAME and "manifest" in PurePosixPath(n).name.casefold() and n.casefold().endswith(".csv")]
            if len(manifest_candidates) != 1:
                errors.append(f"archive must contain exactly one root {MANIFEST_NAME}")
            if other_manifest_csv:
                errors.append("additional manifest-like CSV files are prohibited: " + ", ".join(sorted(other_manifest_csv)))
            if errors:
                # Container/path failures are terminal: do not dereference any
                # questionable archive member.
                return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}

            manifest_info = archive.getinfo(MANIFEST_NAME)
            if manifest_info.file_size > MAX_MANIFEST_BYTES:
                errors.append("manifest exceeds fixed byte ceiling")
                return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}
            try:
                manifest_data = archive.read(manifest_info)
            except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
                errors.append(f"manifest CRC/read failure: {exc}")
                return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}
            by_path, by_role = _parse_manifest(manifest_data, names, errors)
            if errors:
                return {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": errors, "warnings": warnings, "metrics": metrics}

            # Full streaming read verifies CRC for every member.  Do not trust
            # central-directory sizes or hashes without observing every byte.
            for info in infos:
                if info.filename == MANIFEST_NAME:
                    continue
                digest = hashlib.sha256()
                crc = 0
                count = 0
                chunks: list[bytes] = []
                role = by_path[info.filename]["role"]
                capture = role in TEXT_ROLES
                if capture and info.file_size > MAX_TEXT_EVIDENCE_BYTES:
                    errors.append(f"member {info.filename!r}: required text evidence exceeds {MAX_TEXT_EVIDENCE_BYTES} bytes")
                    capture = False
                prefix = b""
                marker_found: str | None = None
                marker_tail = b""
                try:
                    with archive.open(info, "r") as member:
                        while True:
                            chunk = member.read(1024 * 1024)
                            if not chunk:
                                break
                            if not prefix:
                                prefix = chunk[:8]
                            count += len(chunk)
                            if count > MAX_MEMBER_BYTES or count > info.file_size:
                                raise ContractError("streamed bytes exceed declared/fixed member size")
                            digest.update(chunk)
                            crc = zlib.crc32(chunk, crc)
                            if marker_found is None:
                                marker_found = _prohibited_bytes(marker_tail + chunk)
                                marker_tail = (marker_tail + chunk)[-128:]
                            if capture:
                                chunks.append(chunk)
                except (zipfile.BadZipFile, RuntimeError, OSError, ContractError) as exc:
                    errors.append(f"member {info.filename!r}: CRC/read failure: {exc}")
                    continue
                actual[info.filename] = {
                    "bytes": count,
                    "sha256": digest.hexdigest(),
                    "crc32": crc & 0xFFFFFFFF,
                    "prefix": prefix,
                    "production_marker": marker_found,
                }
                if capture:
                    contents[info.filename] = b"".join(chunks)
                row = by_path[info.filename]
                if count != info.file_size or (crc & 0xFFFFFFFF) != info.CRC:
                    errors.append(f"member {info.filename!r}: declared ZIP size/CRC mismatch")
                if row["bytes"] != count:
                    errors.append(f"member {info.filename!r}: manifest byte count mismatch")
                if row["sha256"] != digest.hexdigest():
                    errors.append(f"member {info.filename!r}: manifest SHA-256 mismatch")

            history = actual.get(REQUIRED_ROLE_PATHS["bridge_history"])
            if history and not history["prefix"].startswith(b"PK\x03\x04"):
                errors.append("bridge_history: .npz evidence is not a real nonempty ZIP/NPZ container")
    except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError) as exc:
        errors.append(f"ZIP parse failure: {exc}")

    if not errors:
        contract_data = contents.get(CONTRACT_NAME)
        if contract_data is None:
            errors.append("contract bytes unavailable")
        else:
            try:
                contract = _json_no_duplicates(contract_data, CONTRACT_NAME)
            except ContractError as exc:
                errors.append(str(exc))
            else:
                metrics.update(
                    _validate_contract(
                        contract,
                        by_role,
                        actual,
                        contents,
                        require_production=require_production,
                        expected=expected,
                        errors=errors,
                    )
                )
    if not errors:
        try:
            from dmde_v0920_validate_bbn_canary import validate_bbn_canary
            from dmde_v0920_validate_weak_rate_closure import validate_weak_rate_closure

            with tempfile.TemporaryDirectory(prefix="dmde_v0920_raw_standalone_") as temp_name:
                with zipfile.ZipFile(path, "r") as archive:
                    # All members have already passed the canonical container,
                    # path, symlink, CRC, and manifest checks above.
                    archive.extractall(temp_name)
                extracted_root = Path(temp_name)
                weak_result = validate_weak_rate_closure(
                    extracted_root / REQUIRED_ROLE_PATHS["bridge_history"],
                    extracted_root / REQUIRED_ROLE_PATHS["weak_rate_closure_metadata"],
                )
                bbn_result = validate_bbn_canary(
                    extracted_root / REQUIRED_ROLE_PATHS["bbn_canary_contract"],
                )
                metrics["weak_rate_causal_closure"] = weak_result
                metrics["bbn_consumption_canary"] = bbn_result
                if weak_result.get("status") != "PASS":
                    errors.append(
                        "weak-rate causal closure failed: "
                        + " | ".join(weak_result.get("errors", ["unknown failure"]))
                    )
                if bbn_result.get("status") != "PASS":
                    errors.append(
                        "BBN consumption canary failed: "
                        + " | ".join(bbn_result.get("errors", ["unknown failure"]))
                    )
        except Exception as exc:
            errors.append(f"causal evidence validation failure: {exc}")
    return {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def validate_raw_evidence(
    archive_path,
    bridge_npz_path,
    bridge_metadata_path,
    expected_identity: dict[str, Any],
    *,
    expected_run_role: str,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    """Programmatic adapter used by the v0.9.20 provider-return firewall."""
    bridge_npz_path = Path(bridge_npz_path)
    bridge_metadata_path = Path(bridge_metadata_path)
    expected = {
        "blind_id": expected_identity["blind_id"],
        "source_payload_sha256": expected_identity["source_payload_sha256"],
        "bridge_history_sha256": hashlib.sha256(bridge_npz_path.read_bytes()).hexdigest(),
        "bridge_metadata_sha256": hashlib.sha256(bridge_metadata_path.read_bytes()).hexdigest(),
        "run_class": "conformance" if allow_synthetic else "production",
        "run_role": expected_run_role,
    }
    result = validate_archive_file(
        archive_path,
        require_production=not allow_synthetic,
        expected=expected,
    )
    if result.get("status") != "PASS":
        return result
    linkage_errors: list[str] = []
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            weak_text = archive.read(REQUIRED_ROLE_PATHS["weak_rates"]).decode("utf-8")
            bbn_rate_text = archive.read(REQUIRED_ROLE_PATHS["bbn_rate_input"]).decode("utf-8")
            solver_config = _json_no_duplicates(
                archive.read(REQUIRED_ROLE_PATHS["solver_config"]),
                "solver_config",
            )
            operator_receipt = _json_no_duplicates(
                archive.read(REQUIRED_ROLE_PATHS["operator_probe_receipt"]),
                "operator_probe_receipt",
            )
            final_outputs = _json_no_duplicates(archive.read(REQUIRED_ROLE_PATHS["final_outputs"]), "final_outputs")
        reader = csv.DictReader(io.StringIO(weak_text, newline=""))
        weak_rows = list(reader)
        bbn_reader = csv.DictReader(io.StringIO(bbn_rate_text, newline=""))
        bbn_rows = list(bbn_reader)
        with np.load(bridge_npz_path, allow_pickle=False) as bridge:
            t = np.asarray(bridge["t_s"], dtype=float)
            temperature = np.asarray(bridge["T_gamma_MeV"], dtype=float)
            hubble = np.asarray(bridge["H_s_inv"], dtype=float)
            rate_np = np.asarray(bridge["lambda_n_to_p_s_inv"], dtype=float)
            rate_pn = np.asarray(bridge["lambda_p_to_n_s_inv"], dtype=float)
            q_grid = np.asarray(bridge["q_grid"])
            witness_indices = np.rint(np.asarray(bridge["source_stepper_time_index"], dtype=float)).astype("<i8")
            state_species = ("nue", "nuebar", "numu", "numubar", "nutau", "nutaubar")
            computed_state_hashes = []
            for witness_row, history_index in enumerate(witness_indices):
                digest = hashlib.sha256()
                digest.update(np.asarray(history_index, dtype="<i8").tobytes())
                for species in state_species:
                    values = np.asarray(
                        bridge[f"source_stepper_initial_state_dYdq_{species}"][witness_row],
                        dtype="<f8",
                    )
                    digest.update(values.tobytes(order="C"))
                computed_state_hashes.append(digest.hexdigest())
            if not isinstance(operator_receipt, dict) or operator_receipt.get("state_hashes") != computed_state_hashes:
                linkage_errors.append("operator_probe_receipt state hashes disagree with external bridge witness states")
            if not isinstance(solver_config, dict) or solver_config.get("momentum_bins") != len(q_grid):
                linkage_errors.append("solver_config momentum_bins disagrees with external bridge q_grid")
            if len(weak_rows) != len(t):
                linkage_errors.append("weak_rates CSV row count disagrees with external bridge")
            else:
                raw_t = np.asarray([float(row["time_s"]) for row in weak_rows])
                raw_np = np.asarray([float(row["lambda_n_to_p_s_inv"]) for row in weak_rows])
                raw_pn = np.asarray([float(row["lambda_p_to_n_s_inv"]) for row in weak_rows])
                for label, raw_values, bridge_values in (
                    ("time", raw_t, t), ("lambda_n_to_p", raw_np, rate_np),
                    ("lambda_p_to_n", raw_pn, rate_pn),
                ):
                    if not np.array_equal(raw_values, bridge_values):
                        linkage_errors.append(f"weak_rates CSV {label} values are not byte-value identical to external bridge")
            if len(bbn_rows) != len(t):
                linkage_errors.append("bbn_rate_input CSV row count disagrees with external bridge")
            else:
                bbn_arrays = {
                    key: np.asarray([float(row[key]) for row in bbn_rows])
                    for key in (
                        "time_s", "T_gamma_MeV", "H_s_inv",
                        "lambda_n_to_p_s_inv", "lambda_p_to_n_s_inv",
                    )
                }
                for label, raw_values, bridge_values in (
                    ("time", bbn_arrays["time_s"], t),
                    ("T_gamma", bbn_arrays["T_gamma_MeV"], temperature),
                    ("H", bbn_arrays["H_s_inv"], hubble),
                    ("lambda_n_to_p", bbn_arrays["lambda_n_to_p_s_inv"], rate_np),
                    ("lambda_p_to_n", bbn_arrays["lambda_p_to_n_s_inv"], rate_pn),
                ):
                    if not np.array_equal(raw_values, bridge_values):
                        linkage_errors.append(
                            f"bbn_rate_input CSV {label} values are not byte-value identical to external bridge"
                        )
            for json_key, npz_key in (
                ("Yp_model", "Yp_model"), ("DH_x1e5_model", "DH_x1e5_model"),
                ("Neff_CMB_model", "Neff_CMB_model"),
            ):
                if not math.isclose(float(final_outputs[json_key]), float(np.asarray(bridge[npz_key]).reshape(-1)[0]), rel_tol=0, abs_tol=1e-14):
                    linkage_errors.append(f"final_outputs {json_key} disagrees with external bridge")
    except Exception as exc:
        linkage_errors.append(f"external raw/bridge semantic linkage failure: {exc}")
    if linkage_errors:
        result["status"] = "FAIL"
        result.setdefault("errors", []).extend(linkage_errors)
    return result


def _load_expected(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    value = _json_no_duplicates(data, "expected context")
    if not isinstance(value, dict):
        raise ContractError("expected context must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive_ref", help="POSIX-style relative path under --base")
    parser.add_argument("--base", default=".", help="trusted base for external path resolution")
    parser.add_argument("--expected-context", help="optional relative JSON path under --base")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    try:
        archive = safe_resolve_external(args.base, args.archive_ref)
        expected = None
        if args.expected_context:
            expected_path = safe_resolve_external(args.base, args.expected_context)
            expected = _load_expected(expected_path)
        result = validate_archive_file(archive, require_production=True, expected=expected)
    except (ContractError, OSError) as exc:
        result = {"schema": SCHEMA_VERSION, "status": "FAIL", "errors": [str(exc)], "warnings": [], "metrics": {}}
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
