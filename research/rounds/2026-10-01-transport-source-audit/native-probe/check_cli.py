#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Check evidence preservation and failure reporting in the local wrapper only.

The controlled subprocess failure is a harness test, not a native-RHS mock.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).parent
WRAPPER = ROOT / "native_probe_final.py"
OUT = ROOT / "cli-checks-2026-10-01-r2"
OUT.mkdir(exist_ok=False)
checks = []
for name, options, cli, extra_env in [
    ("reject_optimized_flag", ["-O"], ["run-rhs"], {}),
    ("reject_optimized_environment", [], ["run-rhs"], {"PYTHONOPTIMIZE": "1"}),
    ("reject_invalid_even_grid", [], ["emission", "--domain", "complete", "--n", "20"], {}),
    ("reject_missing_emission_grid", [], ["emission"], {}),
]:
    candidate = OUT / name
    result = subprocess.run([sys.executable, "-B", *options, str(WRAPPER), *cli, "--out", str(candidate)],
                            env={**os.environ, **extra_env}, capture_output=True, text=True)
    (OUT / f"{name}.stderr.log").write_text(result.stderr)
    passed = result.returncode != 0 and not candidate.exists()
    checks.append({"name": name, "returncode": result.returncode, "output_created": candidate.exists(), "passed": passed})

existing = OUT / "existing_evidence"
existing.mkdir()
(existing / "sentinel.txt").write_text("preserved\n")
result = subprocess.run([sys.executable, "-B", str(WRAPPER), "run-rhs", "--out", str(existing)],
                        capture_output=True, text=True)
(OUT / "reject_existing_output.stderr.log").write_text(result.stderr)
checks.append({"name": "reject_existing_output", "returncode": result.returncode,
               "passed": result.returncode != 0 and (existing / "sentinel.txt").read_text() == "preserved\n" and len(list(existing.iterdir())) == 1})

spec = importlib.util.spec_from_file_location("local_probe_cli_check", WRAPPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
failure = OUT / "controlled_spawn_failure"
controlled_result = subprocess.CompletedProcess(["controlled harness failure; no physics called"], 7, "", "controlled test failure\n")
raised = False
real_run = subprocess.run
def controlled_run(command, *args, **kwargs):
    if str(WRAPPER) in command and "rhs" in command:
        return controlled_result
    return real_run(command, *args, **kwargs)
with patch.object(module.subprocess, "run", side_effect=controlled_run):
    try:
        module.run(failure, rhs_only=True)
    except RuntimeError:
        raised = True
receipt = json.loads((failure / "execution.json").read_text())
checks.append({"name": "propagate_controlled_worker_failure", "scope": "orchestration harness only; no native physics call",
               "worker_returncode": receipt["jobs"][0]["returncode"],
               "passed": raised and not receipt["all_jobs_completed_successfully"] and receipt["source_unchanged"]})

with (OUT / "result.json").open("x") as handle:
    json.dump({"checks": checks, "all_passed": all(c["passed"] for c in checks)}, handle, indent=2)
    handle.write("\n")
print(json.dumps({"checks": len(checks), "all_passed": all(c["passed"] for c in checks)}))
if not all(c["passed"] for c in checks):
    raise RuntimeError("Local wrapper CLI check failed")
