#!/usr/bin/env python3
"""Replay public numerical controls, retaining a new provenance dossier.

This is maintenance/reproduction, not an AI researcher or a DMDE prediction.
No private checkout, network request, solver source, or credential is consumed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(base, manifest):
    entries = json.loads(manifest.read_text())
    for name, expected in entries.items():
        relative = Path(name)
        target = (base / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(base.resolve()):
            raise ValueError("Unsafe receipt-manifest path")
        if sha(target) != expected:
            raise ValueError(f"Receipt hash mismatch: {name}")
    return len(entries)


def snapshot():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    return {name: sha(ROOT / name) for name in names if name}


def check_reviewed_sources(manifest):
    entries = json.loads(manifest.read_text())
    documentation_changes = []
    numerical_count = 0
    for name, expected in entries.items():
        target = (ROOT / name).resolve()
        if Path(name).is_absolute() or ".." in Path(name).parts or not target.is_relative_to(ROOT):
            raise ValueError("Unsafe reviewed-source path")
        actual = sha(target) if target.is_file() else None
        if name.endswith(".py"):
            numerical_count += 1
            if actual != expected:
                raise ValueError(f"Historically reviewed numerical source changed: {name}")
        elif actual != expected:
            documentation_changes.append(name)
    return {
        "entries": len(entries), "unchanged_numerical_sources": numerical_count,
        "documentation_changed_since_review": documentation_changes,
        "historical_review_covers_current_documents": not documentation_changes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New directory strictly below this checkout's generated/ directory.")
    args = parser.parse_args()
    if sys.flags.optimize or os.environ.get("PYTHONOPTIMIZE", "") not in ("", "0"):
        parser.error("Python optimization disables historical assertions; use ordinary Python.")
    output = args.output_dir.resolve()
    if GENERATED.is_symlink() or not GENERATED.resolve().is_relative_to(ROOT):
        parser.error("generated/ must be an ordinary directory within this checkout.")
    if not output.is_relative_to(GENERATED.resolve()) or output == GENERATED.resolve():
        parser.error("Output must be a new directory strictly below generated/.")
    if output.exists():
        parser.error("Refusing to overwrite an existing round.")
    GENERATED.mkdir(exist_ok=True)
    with (GENERATED / ".dmde-round.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another numerical round is already running.")
        output.mkdir(parents=True, exist_ok=False)
        before = None
        receipt = {
            "kind": "PUBLIC_NUMERICAL_MAINTENANCE_REPRODUCTION",
            "scope": "No new transport solve, BBN prediction, literature search, AI research, or discovery.",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "steps": [], "status": "FAIL",
        }
        env = os.environ.copy()
        for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
            env[key] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        py = [sys.executable, "-B"]
        audit = "research/2026-10-01-equilibrium-audit"
        review = "research/2026-10-01-independent-review"
        steps = [
            ("release-integrity", ["scripts/check_public_release.py"]),
            ("deep-payloads", ["provider/code/dmde_v0920_validate_blind_payloads_deep.py", "--base", "provider", "--out-csv", str(output / "deep.csv"), "--out-json", str(output / "deep.json")]),
            ("pair-geometry", ["provider/code/dmde_v0920_pair_geometry.py", "--provider-root", "provider", "--json-out", str(output / "geometry.json"), "--csv-out", str(output / "precision.csv")]),
            ("equilibrium-tests", ["-m", "unittest", "discover", "-s", audit, "-p", "test_*.py", "-v"]),
            ("equilibrium-report", [audit + "/equilibrium_audit.py", "--output-dir", str(output / "equilibrium")]),
            ("independent-integration", [review + "/independent_rates.py", "--output", str(output / "independent.json")]),
            ("independent-comparison", [review + "/compare_with_producer.py", "--producer-dir", audit, "--output", str(output / "comparison.json")]),
            ("saved-sm-controls", ["research/2026-10-01-sm-control/verify_controls.py", "--output", str(output / "historical-controls.json")]),
        ]
        try:
            before = snapshot()
            receipt.update({
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "tracked_worktree_clean_at_start": subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT).returncode == 0,
                "numpy": version("numpy"), "scipy": version("scipy"),
                "round_driver_sha256": sha(Path(__file__)),
                "public_source_fingerprint_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
            })
            receipt["verified_saved_manifest_entries"] = {
                "sm": verify_manifest(ROOT / "research/2026-10-01-sm-control", ROOT / "research/2026-10-01-sm-control/ARTIFACT_SHA256.json"),
                "review": verify_manifest(ROOT / review, ROOT / review / "REVIEW_ARTIFACT_SHA256.json"),
            }
            receipt["reviewed_source_provenance"] = check_reviewed_sources(ROOT / review / "reviewed_sources_sha256.json")
            for label, arguments in steps:
                log = output / (label + ".log")
                step = {"name": label, "command": py + arguments, "log": log.name, "status": "RUNNING"}
                receipt["steps"].append(step)
                with log.open("x") as stream:
                    try:
                        result = subprocess.run(py + arguments, cwd=ROOT, env=env,
                                                stdout=stream, stderr=subprocess.STDOUT, timeout=300)
                    except subprocess.TimeoutExpired:
                        step["status"] = "TIMEOUT"
                        raise
                step.update({"returncode": result.returncode, "status": "PASS" if result.returncode == 0 else "FAIL"})
                if result.returncode:
                    raise RuntimeError(f"Check failed: {label}")
            receipt["status"] = "PASS_REPRODUCTION_ONLY"
        except Exception as error:
            receipt["failure"] = str(error)
            if receipt["steps"] and receipt["steps"][-1]["status"] == "RUNNING":
                receipt["steps"][-1]["status"] = "ERROR"
        finally:
            try:
                receipt["tracked_files_unchanged"] = before is not None and snapshot() == before
            except Exception as error:
                receipt["tracked_files_unchanged"] = False
                receipt["final_source_check_failure"] = str(error)
            if not receipt["tracked_files_unchanged"]:
                receipt["status"] = "FAIL"
                receipt["source_integrity_failure"] = (
                    "Initial tracked-file identity could not be verified." if before is None
                    else "Tracked files changed, or final tracked-file identity could not be verified."
                )
                receipt.setdefault("failure", receipt["source_integrity_failure"])
            receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
            (output / "ROUND_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
            artifacts = {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob("*")) if p.is_file()}
            (output / "ARTIFACT_SHA256.json").write_text(json.dumps(artifacts, indent=2) + "\n")
        print(receipt["status"])
        print(f"New public reproduction dossier: {output}")
        return 0 if receipt["status"] == "PASS_REPRODUCTION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
