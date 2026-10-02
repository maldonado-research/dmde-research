#!/usr/bin/env python3
"""Review driver failure handling with mocked commands and temporary /tmp roots.

These checks never execute the scientific controls, access private material,
contact a network service, or modify the reviewed checkout. A passing review
establishes the listed orchestration behaviors only.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import PackageNotFoundError
import importlib.util
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite a historical review receipt.")
    spec = importlib.util.spec_from_file_location("reviewed_round_driver", args.driver.resolve())
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    outcomes = []

    def review(name, test):
        try:
            with TemporaryDirectory(prefix="dmde-mocked-review-", dir="/tmp") as temp:
                root = Path(temp) / "checkout"
                root.mkdir()
                driver.ROOT = root
                driver.GENERATED = root / "generated"
                test(root)
            outcomes.append({"name": name, "status": "PASS"})
        except Exception as error:
            outcomes.append({"name": name, "status": "FAIL", "failure": str(error)})

    def replay(root, *, snapshots=None, missing_package=False, step_error=None, step_returncode=0):
        output = root / "generated" / "review-round"
        def run(command, **kwargs):
            if command[0] == "git":
                return subprocess.CompletedProcess(command, 0)
            if step_error == "timeout":
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            if step_error == "oserror":
                raise OSError("synthetic subprocess-start failure")
            return subprocess.CompletedProcess(command, step_returncode)
        snapshot_args = {"side_effect": snapshots} if snapshots is not None else {"return_value": {}}
        version_args = {"side_effect": PackageNotFoundError("synthetic-missing-numpy")} if missing_package else {"return_value": "mocked-metadata"}
        with patch.object(driver, "snapshot", **snapshot_args), patch.object(driver, "version", **version_args), patch.object(driver, "verify_manifest", return_value=7), patch.object(driver, "check_reviewed_sources", return_value={"scope": "mocked provenance"}), patch.object(driver.subprocess, "check_output", return_value="mocked-source-commit\n"), patch.object(driver.subprocess, "run", side_effect=run), patch.object(sys, "argv", ["review", "--output-dir", str(output)]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = driver.main()
        receipt = json.loads((output / "ROUND_RECEIPT.json").read_text())
        hashes = json.loads((output / "ARTIFACT_SHA256.json").read_text())
        require(hashes.get("ROUND_RECEIPT.json") == sha(output / "ROUND_RECEIPT.json"), "Receipt artifact hash must match.")
        require(all(sha(output / name) == expected for name, expected in hashes.items()), "Every declared artifact hash must match.")
        return status, receipt

    def missing_dependency(root):
        status, receipt = replay(root, missing_package=True)
        require(status == 1 and receipt["status"] == "FAIL", "Missing metadata must fail with a receipt.")
        require("synthetic-missing-numpy" in receipt.get("failure", ""), "Original dependency failure must be retained.")

    def initial_snapshot_failure(root):
        status, receipt = replay(root, snapshots=[FileNotFoundError("synthetic initial snapshot failure")])
        require(status == 1 and receipt["status"] == "FAIL", "Initial snapshot failure must produce a FAIL receipt.")
        require("synthetic initial snapshot failure" in json.dumps(receipt), "Original initial snapshot error must be retained.")

    def final_snapshot_failure(root):
        status, receipt = replay(root, snapshots=[{}, FileNotFoundError("synthetic final snapshot failure")])
        require(status == 1 and receipt["status"] == "FAIL", "Final snapshot failure must override successful mocked steps.")
        require(receipt["tracked_files_unchanged"] is False and "synthetic final snapshot failure" in receipt.get("final_source_check_failure", ""), "Final source-check error must be retained.")
        require(len(receipt["steps"]) == 8, "All eight completed mocked step records must remain.")

    def timeout_failure(root):
        status, receipt = replay(root, step_error="timeout")
        require(status == 1 and receipt["status"] == "FAIL", "Timeout must fail.")
        require(len(receipt["steps"]) == 1 and receipt["steps"][0]["status"] == "TIMEOUT", "Timed-out attempt must be recorded.")
        require("timed out after 300 seconds" in receipt.get("failure", ""), "Timeout reason must remain.")

    def subprocess_failure(root):
        status, receipt = replay(root, step_returncode=23)
        require(status == 1 and receipt["status"] == "FAIL", "Nonzero subprocess exit must fail.")
        require(receipt["steps"][0]["returncode"] == 23 and receipt["steps"][0]["status"] == "FAIL", "Actual subprocess code must be retained.")

    def subprocess_start_failure(root):
        status, receipt = replay(root, step_error="oserror")
        require(status == 1 and receipt["status"] == "FAIL", "Subprocess-start failure must fail.")
        require(receipt["steps"][0]["status"] == "ERROR", "Attempted subprocess must be marked ERROR.")

    def rejected_output(root, nested=False):
        outside = root.parent / "outside"
        outside.mkdir()
        if nested:
            driver.GENERATED.mkdir()
            (driver.GENERATED / "escape").symlink_to(outside, target_is_directory=True)
            output = driver.GENERATED / "escape" / "new-round"
        else:
            driver.GENERATED.symlink_to(outside, target_is_directory=True)
            output = driver.GENERATED / "new-round"
        with patch.object(sys, "argv", ["review", "--output-dir", str(output)]), redirect_stderr(io.StringIO()):
            try:
                driver.main()
            except SystemExit as error:
                require(error.code == 2, "Escaping output must be rejected by argument guard.")
            else:
                raise AssertionError("Escaping output was accepted.")
        require(not (outside / "new-round").exists(), "Rejected output must never be created outside checkout.")

    def lock_guard(root):
        driver.GENERATED.mkdir()
        output = driver.GENERATED / "new-round"
        with (driver.GENERATED / ".dmde-round.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(sys, "argv", ["review", "--output-dir", str(output)]), redirect_stderr(io.StringIO()):
                try:
                    driver.main()
                except SystemExit as error:
                    require(error.code == 2, "Concurrent invocation must be rejected.")
                else:
                    raise AssertionError("Concurrent invocation was accepted.")
        require(not output.exists(), "Concurrent rejection must occur before creating output.")

    def document_provenance(root):
        source = root / "numeric.py"
        doc = root / "claims.md"
        source.write_text("# synthetic unchanged numerical source\n")
        doc.write_text("Historical synthetic documentation.\n")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"numeric.py": sha(source), "claims.md": sha(doc)}))
        doc.write_text("Revised synthetic documentation.\n")
        result = driver.check_reviewed_sources(manifest)
        require(result["unchanged_numerical_sources"] == 1 and result["documentation_changed_since_review"] == ["claims.md"] and result["historical_review_covers_current_documents"] is False, "Changed documentation must be explicitly outside historical review without blocking unchanged code.")
        source.write_text("# changed synthetic numerical source\n")
        try:
            driver.check_reviewed_sources(manifest)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed historically reviewed numerical code was accepted.")

    def manifest_containment(root):
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({"../outside": "0" * 64}))
        for checker in [lambda: driver.check_reviewed_sources(manifest), lambda: driver.verify_manifest(root, manifest)]:
            try:
                checker()
            except ValueError:
                pass
            else:
                raise AssertionError("Manifest traversal was accepted.")

    review("missing-dependency-failure-receipt", missing_dependency)
    review("initial-snapshot-failure-receipt-and-cause", initial_snapshot_failure)
    review("final-snapshot-failure-receipt", final_snapshot_failure)
    review("timeout-attempt-record", timeout_failure)
    review("nonzero-subprocess-exit-record", subprocess_failure)
    review("subprocess-start-error-record", subprocess_start_failure)
    review("generated-symlink-escape-rejection", rejected_output)
    review("nested-output-symlink-escape-rejection", lambda root: rejected_output(root, nested=True))
    review("concurrent-local-round-rejection", lock_guard)
    review("historical-document-and-numerical-source-semantics", document_provenance)
    review("manifest-path-containment", manifest_containment)
    receipt = {
        "review_kind": "MOCKED_ORCHESTRATION_AND_PATH_GUARD_REVIEW",
        "scope": "Temporary /tmp roots and mocked subprocesses only; no scientific control, fresh solver, private input, credential or network operation executed.",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "review_source_sha256": sha(Path(__file__)),
        "round_driver_sha256": sha(args.driver),
        "tests": outcomes,
        "pass_count": sum(row["status"] == "PASS" for row in outcomes),
        "fail_count": sum(row["status"] == "FAIL" for row in outcomes),
        "status": "PASS_ORCHESTRATION_ONLY" if all(row["status"] == "PASS" for row in outcomes) else "FAIL",
    }
    with args.output.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
