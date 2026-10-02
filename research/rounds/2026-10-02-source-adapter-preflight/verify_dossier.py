#!/usr/bin/env python3
"""Verify recorded identities and scope of this public preflight dossier.

No external solver is executed. A passing receipt check preserves, rather than
overturns, the explicitly recorded physics failures.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read(relative):
    return json.loads((ROOT / relative).read_text())


def check_map(base, mapping):
    require(isinstance(mapping, dict) and bool(mapping), 'Empty/invalid manifest')
    for name, expected in mapping.items():
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts,
                f'Invalid manifest path: {name}')
        require(isinstance(expected, str) and re.fullmatch(r'[0-9a-f]{64}', expected),
                f'Invalid digest: {name}')
        target = base / name
        require(target.is_file() and not target.is_symlink(), f'Missing/unsafe file: {target}')
        require(target.resolve().is_relative_to(base.resolve()), f'Escaping file: {target}')
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        require(actual == expected, f'Identity mismatch: {target}')
    return len(mapping)


def main():
    manifest = read('ARTIFACT_SHA256.json')
    files = manifest['file_sha256']
    count = check_map(ROOT, files)
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
    require(actual == set(files) | {'ARTIFACT_SHA256.json'}, 'Inventory differs from selection')
    inner_counts = {
        'domain': check_map(ROOT / 'domain', read('domain/ARTIFACT_SHA256.json')),
        'conservation': check_map(ROOT / 'conservation', read('conservation/ARTIFACT_SHA256.json')['files']),
        'runtime': check_map(ROOT / 'runtime', read('runtime/bundle_manifest.json')['file_sha256']),
        'peer': check_map(ROOT / 'peer', read('peer/PEER_ARTIFACT_SHA256.json')['files']),
        'review': check_map(ROOT / 'review',
                            {k: v['sha256'] for k, v in read('review/bundle_manifest.json')['members'].items()}),
    }
    native = read('runtime/results-serialization-fix/native_fixed_state/result.json')
    require(len(native['checks']) == 12 and all(v is True for v in native['checks'].values()),
            'Saved local adapter checks do not all pass')
    require(native['trajectory_integrated'] is False, 'Fixture must remain a nontrajectory')
    negative = native['frozen_preoscillation_source_infinitesimal_RHS_comparison']
    require(negative['passed'] is False and negative['preoscillation_tau_peak'] == 0
            and negative['native_full_RHS_source_tau_peak'] > 0
            and negative['error_relative_to_preoscillation_source_peak'] > negative['relative_ceiling'],
            'Known native unsplit-source negative was lost')
    witness = read('runtime/results-serialization-fix/native_fixed_state/coefficient_witness.json')
    require(witness['coefficient_error_relative_peak'] <= witness['coefficient_tolerance'],
            'Saved native source coefficient witness failed')
    for prefix in ['runtime/results-serialization-fix',
                   'runtime/results-serialization-fix/native_fixed_state',
                   'domain/results-hardened-declared-replay',
                   'domain/results-hardened-phase-replay']:
        before = read(prefix + '/source_before.json')
        after = read(prefix + '/source_after.json')
        require(before == after, f'Upstream identity changed: {prefix}')
    phase = read('domain/results-hardened-phase-replay/results.json')['rows']
    require([row['n'] for row in phase] == [3001, 4001, 8001], 'Unexpected phase ladder')
    require([row['all_scanned_rows_k0_to_k5_pass'] for row in phase] == [False, True, True],
            'Recorded phase-scan outcomes changed')
    domain = read('domain/results-hardened-declared-replay/source_grid_results.json')
    full = [row for row in domain['rows'] if row['case'] == 'full_reference_cap_native_weights']
    require({row['n'] for row in full} == {301, 1001, 3001, 10001},
            'Full-reference ladder changed')
    require(all(any(not row['all_k0_to_k5_within_005'] for row in full if row['n'] == n)
                for n in {301, 1001, 3001, 10001}),
            'Known full-domain failures were lost')
    failed = read('runtime/results-first/execution.json')
    require(failed['returncode'] != 0 and failed['source_unchanged'] is True,
            'Original serialization failure was lost')
    components = read('conservation/qed_component_reference.json')
    require(components['native_symbols_modified'] is False
            and components['native_constants_modified'] is False
            and components['source_unchanged'] is True, 'Component scope changed')
    require(len(components['observations']) == 9, 'Unexpected QED refinement inventory')
    pressure_error = max(abs(row[key]) for row in components['observations']
                         for key in ['rho2_reference_minus_complex_step_pressure_identity',
                                     'rho3_reference_minus_complex_step_pressure_identity'])
    require(pressure_error < 1e-12, 'Saved component pressure identity failed')
    replay = read('PUBLIC_COPY_REPLAY.json')
    require(replay['status'] == 'PASS' and replay['raw_runtime_csv_exact_matches'] > 0
            and replay['qed_observations_exact_match'] is True
            and replay['source_unchanged'] is True,
            'Public-copy replay evidence failed')
    require(replay['raw_runtime_csv_exact_matches'] == len(replay['raw_runtime_csv_sha256']),
            'Raw replay inventory count changed')
    check_map(ROOT / 'runtime/results-serialization-fix/native_fixed_state',
              replay['raw_runtime_csv_sha256'])
    independent = read('public-copy-review/runtime-review/runtime_artifact_independent_review.json')
    require(independent['production_source_accumulator_directly_instrumented'] is False
            and independent['finite_steps_h_and_h2_executed'] is False
            and independent['transport_trajectory_executed'] is False,
            'Independent review scope changed')
    require(independent['independent_raw_RHS_source_coefficient_peak_scaled_error'] < 1e-12
            and independent['coarse_grid_finite_domain_moment_gate_passed'] is False,
            'Independent coefficient or known coarse-grid finding changed')
    print(json.dumps({'status': 'PASS', 'selected_files': count,
                      'component_manifests': inner_counts,
                      'local_adapter_checks': 12,
                      'known_physics_negatives_preserved': True,
                      'scope': 'Recorded identity/receipt verification; no native replay or physical validation'},
                     sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'Preflight dossier verification failed: {error}', file=sys.stderr)
        sys.exit(1)
