"""Check recording/replay and optimization refusals; stdout unless --output."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def require(condition, description):
    if not condition:
        raise RuntimeError(description)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--nudec-dir", type=Path, default=Path("/workspace/shared/dmde-upstream/nudec"))
    parser.add_argument("--primat-dir", type=Path, default=Path("/workspace/shared/dmde-upstream/primat"))
    parser.add_argument("--previous-receipt", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f"Refusing to overwrite existing output: {args.output}")
    root = Path(__file__).resolve().parent
    scientific_receipt = root / "source_coverage.json"
    command = [sys.executable, str(root / "source_coverage.py"),
               "--nudec-dir", str(args.nudec_dir), "--primat-dir", str(args.primat_dir)]
    protected = [root / name for name in ("source_coverage.py", "source_coverage.json", "README.md", "verify_coverage.py")]
    def hashes():
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    initial = hashes()
    run = subprocess.run(command, check=True, capture_output=True, text=True)
    expected = scientific_receipt.read_text()
    baseline = json.loads(expected)
    executed = json.loads(run.stdout)
    baseline_without_runtime = {key: value for key, value in baseline.items() if key != "runtime"}
    executed_without_runtime = {key: value for key, value in executed.items() if key != "runtime"}
    require(json.dumps(executed_without_runtime, sort_keys=True, allow_nan=False)
            == json.dumps(baseline_without_runtime, sort_keys=True, allow_nan=False),
            "Default replay differs from saved scientific receipt outside runtime metadata")
    require(isinstance(baseline["runtime"], dict) and isinstance(executed["runtime"], dict),
            "Runtime metadata must be objects")
    require(set(baseline["runtime"]) == set(executed["runtime"]), "Runtime metadata keys changed")
    require(all(isinstance(value, str) for runtime in (baseline["runtime"], executed["runtime"])
                for value in runtime.values()), "Runtime version metadata must be strings")
    runtime_differences = {
        key: {"baseline": baseline["runtime"].get(key), "executed": executed["runtime"].get(key)}
        for key in sorted(set(baseline["runtime"]) | set(executed["runtime"]))
        if baseline["runtime"].get(key) != executed["runtime"].get(key)
    }
    require(hashes() == initial, "Default replay modified a protected artifact")
    reject = subprocess.run(command + ["--output", str(scientific_receipt)], capture_output=True, text=True)
    require(reject.returncode == 2 and "Refusing to overwrite" in reject.stderr, "Existing output was not rejected")
    require(hashes() == initial, "Overwrite rejection modified a protected artifact")
    refusals = []
    with tempfile.TemporaryDirectory(prefix="dmde-source-coverage-", dir="/tmp") as temp:
        replay = Path(temp) / "replay.json"
        explicit = subprocess.run(command + ["--output", str(replay)], check=True, capture_output=True, text=True)
        require(replay.read_text() == run.stdout == explicit.stdout, "Fresh explicit output differs from current execution")
        env_zero = dict(os.environ, PYTHONOPTIMIZE="0")
        zero = subprocess.run(command, env=env_zero, capture_output=True, text=True)
        require(zero.returncode == 0 and zero.stdout == run.stdout, "PYTHONOPTIMIZE=0 replay failed")
        for mode in ("-O", "-OO", "environment_nonzero", "runtime_environment_nonzero"):
            output = Path(temp) / (mode + ".json")
            args_output = command[1:] + ["--output", str(output)]
            if mode in ("-O", "-OO"):
                test_command = [sys.executable, mode] + args_output
                result = subprocess.run(test_command, env=env_zero, capture_output=True, text=True)
            elif mode == "environment_nonzero":
                result = subprocess.run([sys.executable] + args_output,
                    env=dict(os.environ, PYTHONOPTIMIZE="1"), capture_output=True, text=True)
            else:
                bootstrap = "import os,runpy,sys; os.environ['PYTHONOPTIMIZE']='1'; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
                result = subprocess.run([sys.executable, "-c", bootstrap] + args_output,
                    env=env_zero, capture_output=True, text=True)
            require(result.returncode == 2 and "require assertions enabled" in result.stderr,
                    f"Optimization mode {mode} was not rejected")
            require(result.stdout == "" and not output.exists(), f"Optimization mode {mode} emitted a receipt")
            refusals.append({"mode": mode, "exit_code": result.returncode,
                             "stdout_empty": True, "requested_output_absent": True})
    require(hashes() == initial, "Interface checks modified a protected artifact")
    previous_check = None
    if args.previous_receipt is not None:
        previous = json.loads(args.previous_receipt.read_text())
        current = json.loads(expected)
        # The intended interface update changes the executed code hash only.
        previous["provenance"].pop("executed_script_sha256")
        current["provenance"].pop("executed_script_sha256")
        require(json.dumps(previous, sort_keys=True, allow_nan=False)
                == json.dumps(current, sort_keys=True, allow_nan=False),
                "Scientific results changed from previous receipt")
        previous_check = {"previous_receipt_sha256": hashlib.sha256(args.previous_receipt.read_bytes()).hexdigest(),
                          "all_fields_except_executed_script_hash_unchanged": True}
    receipt = {
        "controls_all_assertions_passed": executed["controls"]["all_assertions_passed"],
        "default_json_matches_saved_receipt_except_runtime": True,
        "default_stdout_matches_saved_receipt_byte_exact": run.stdout == expected,
        "default_and_repeat_replay_leave_dossier_unchanged": True,
        "explicit_new_output_matches_current_execution_byte_exact": True,
        "overwrite_rejection_exit_code": reject.returncode,
        "rejected_output_unchanged": True,
        "PYTHONOPTIMIZE_zero_replay_passed": True,
        "optimization_refusals": refusals,
        "previous_scientific_receipt_comparison": previous_check,
        "input_artifact_sha256": initial,
        "baseline_runtime": baseline["runtime"],
        "executed_runtime": executed["runtime"],
        "allowed_runtime_differences": runtime_differences,
    }
    rendered = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
