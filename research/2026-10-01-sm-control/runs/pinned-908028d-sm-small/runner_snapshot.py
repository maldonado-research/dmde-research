#!/usr/bin/env python3
"""Record an unmodified upstream PRIMAT SM run, without DMDE model inputs.

Source imports avoid a build or editable installation in the upstream checkout.
All runtime output paths and caches are outside it. Shipped reference caches can
still be read, by PRIMAT's documented overlay contract; this is a control run,
not an independent recomputation of the weak-rate tables.
"""
import argparse
import datetime
import dataclasses
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--network", default="small", choices=["small", "large"])
parser.add_argument("--amax", type=int)
args = parser.parse_args()
source = args.source.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(source))

import numpy as np
from primat.backend import run_bbn
from primat.config import DEFAULT_PARAMS, PRIMATConfig

def git(*arguments):
    return subprocess.check_output(["git", "-C", str(source), *arguments], text=True)

def convert(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Cannot serialize {type(obj)}")

def write(name, value):
    (out / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=convert, allow_nan=False) + "\n")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

initial_status = git("status", "--porcelain=v1", "--untracked-files=all")
if initial_status:
    raise RuntimeError("Upstream checkout is not clean; refusing ambiguous provenance")
tracked = git("ls-files", "-z").split("\0")
write("upstream_tracked_sha256.json", {p: sha(source / p) for p in tracked if p and (source / p).is_file()})
params = {
    "Omegabh2": 0.02242,
    "network": args.network,
    "cache_dir": str(out / "cache"),
    "output_time_evolution": True,
    "output_background_evolution": True,
    "output_final_result": True,
    "output_file": str(out / "abundance_evolution.tsv"),
    "output_background_file": str(out / "background_evolution.tsv"),
    "output_final_file": str(out / "final_abundances.dat"),
    "verbose": True,
}
if args.amax is not None:
    params["amax"] = args.amax
cfg = PRIMATConfig(params)
write("input_overrides.json", params)
write("effective_settings.json", {key: getattr(cfg, key) for key in DEFAULT_PARAMS})
(out / "runner_snapshot.py").write_bytes(Path(__file__).read_bytes())
write("provenance.json", {
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_url": "https://github.com/CyrilPitrou/primat",
    "source_commit": git("rev-parse", "HEAD").strip(),
    "source_tree": git("rev-parse", "HEAD^{tree}").strip(),
    "upstream_commit_date": git("show", "-s", "--format=%cI", "HEAD").strip(),
    "source_path": str(source),
    "upstream_license": "GPL-3.0-or-later",
    "source_status_before": initial_status,
    "backend": "python",
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "installed_packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    "selected_runtime_variables": {key: os.environ.get(key) for key in ["PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"]},
    "runner_sha256": sha(Path(__file__)),
    "argv": sys.argv,
    "interpretation": "Unmodified upstream Standard Model control; not a DMDE prediction, independent physics replication, likelihood, or cache-free rate recomputation.",
})
start = time.perf_counter()
result = run_bbn(params, force_backend="python")
duration = time.perf_counter() - start
write("results.json", result)
final_status = git("status", "--porcelain=v1", "--untracked-files=all")
nuclide_A = {"n": 1, "p": 1, "H2": 2, "H3": 3, "He3": 3, "He4": 4, "He6": 6, "Li6": 6, "Li7": 7, "Be7": 7, "Li8": 8, "B8": 8}
abundances = result["Y_final"]
baryon_sum = sum(nuclide_A[k] * v for k, v in abundances.items()) if all(k in nuclide_A for k in abundances) else None
checks = {
    "elapsed_seconds": duration,
    "source_status_after": final_status,
    "source_clean": final_status == "",
    "positive_final_abundances": all(v >= 0 for v in abundances.values()),
    "all_finite_final_abundances": all(np.isfinite(v) for v in abundances.values()),
    "baryon_number_sum_A_Y": baryon_sum,
    "baryon_number_abs_error": abs(baryon_sum - 1) if baryon_sum is not None else None,
    "physical_helium_fraction": 0 < result["YPBBN"] < 1,
    "positive_deuterium_ratio": result["DoH"] > 0,
}
write("checks.json", checks)
write("output_sha256.json", {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "output_sha256.json"})
print(json.dumps({k: result[k] for k in ["YPBBN", "DoH", "Neff"]}, indent=2))
print(json.dumps(checks, indent=2, default=convert))
if not checks["source_clean"]:
    raise RuntimeError("Upstream checkout changed during execution")
if not checks["positive_final_abundances"] or not checks["all_finite_final_abundances"] or not checks["physical_helium_fraction"]:
    raise RuntimeError("Baseline sanity check failed")
if baryon_sum is not None and abs(baryon_sum - 1) > 1e-10:
    raise RuntimeError("Baryon conservation exceeds upstream reference tolerance")
