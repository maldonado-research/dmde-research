#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Replay producer callback against independent beta-function references."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from finite_domain_reference import (canonical_source, fixed_state_coefficient,
                                     physical_moment, REFERENCE_ELECTRON_MASS_MEV)

parser = argparse.ArgumentParser()
parser.add_argument('--domain', type=Path, required=True)
parser.add_argument('--upstream', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
DOMAIN = args.domain.resolve()
UPSTREAM = args.upstream.resolve()
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=False)
REVIEW_SOURCE = Path(__file__).resolve().parent
(OUT/'executed_review.py').write_bytes(Path(__file__).read_bytes())
(OUT/'finite_domain_reference.py').write_bytes(
    (REVIEW_SOURCE/'finite_domain_reference.py').read_bytes())
sys.dont_write_bytecode = True
sys.path.insert(0, str(DOMAIN))
sys.path.insert(0, str(UPSTREAM))
from source_grid_diagnostic import frozen_michel
import Momentum_Grid


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


configuration = json.loads((DOMAIN / 'predeclaration.json').read_text())
refinement = json.loads((DOMAIN / 'refinement_predeclaration.json').read_text())
snapshot_path = DOMAIN / 'results-first-declared/diagnostic_symmetric_arrays.npz'
scan_path = DOMAIN / 'results-phase-pinned-replay/raw_phase_scan.npz'
producer_result_path = DOMAIN / 'results-phase-pinned-replay/results.json'
producer_results = json.loads(producer_result_path.read_text())
snapshot = np.load(snapshot_path, allow_pickle=False)
reference_sources = np.array([
    canonical_source(snapshot['q'], x, t,
                     configuration['diagnostic_test_card']['tau_s'],
                     configuration['diagnostic_test_card']['Y0'],
                     configuration['diagnostic_test_card']['B_mumu'])
    for x, t in zip(snapshot['x'], snapshot['time_s'])])
species = ('nue', 'nuebar', 'numu', 'numubar', 'nutau', 'nutaubar')
actual_sources = np.stack([snapshot['source_rhs_'+s+'_dYdt_dq_s_inv']
                           for s in species], axis=1)
actual_states = np.stack([snapshot['state_dYdq_'+s] for s in species], axis=1)
occupations = np.stack([snapshot['occupation_'+s] for s in species], axis=1)
expected_states = occupations * fixed_state_coefficient(snapshot['q'])
source_error = float(np.max(np.abs(reference_sources-actual_sources))
                     / np.max(reference_sources))
state_error = float(np.max(np.abs(expected_states-actual_states))
                    / np.max(expected_states))
assert source_error < 1e-12
assert state_error < 1e-12

scan = np.load(scan_path, allow_pickle=False)
rows = []
full_moments = np.array([[physical_moment(a, k, 0, 1e6) for k in range(6)]
                        for a in ('e','mu')])
max_callback_identity_error = 0.0
for n in refinement['native_n_ladder']:
    Momentum_Grid.setupGrid(refinement['q_max'], n, refinement['q_min'])
    q = Momentum_Grid.gridVals
    weights = Momentum_Grid.gridWeights
    reproduced = np.empty((len(scan['x_scan']), 2, 6))
    finite_domain_errors = np.empty_like(reproduced)
    lower_omitted = np.empty_like(reproduced)
    for ti, x in enumerate(scan['x_scan']):
        c = REFERENCE_ELECTRON_MASS_MEV / x
        p = q*c
        callback = frozen_michel(p, x, {'mu':1.})
        # A unit branch/yield/tau and t=0 makes the independent canonical
        # reference exactly c*K(p); select one species from each charge pair.
        independent = canonical_source(q, x, 0.0, 1.0, 1.0, 1.0)[[0,2]]
        max_callback_identity_error = max(max_callback_identity_error,
            float(np.max(np.abs(c*callback[:2]-independent))/np.max(independent)))
        sampled = np.array([[np.sum(weights*c*callback[a]*p**k)
                             for k in range(6)] for a in range(2)])
        finite = np.array([[physical_moment(a,k,p[0],p[-1])
                            for k in range(6)] for a in ('e','mu')])
        reproduced[ti] = sampled/full_moments-1
        finite_domain_errors[ti] = sampled/finite-1
        lower_omitted[ti] = 1-finite/full_moments
    recorded = scan[f'n{n}_relative_moment_errors']
    comparison = float(np.max(np.abs(recorded-reproduced)))
    assert comparison < 1e-12
    reported = next(row for row in producer_results['rows'] if row['n']==n)
    new_worst = np.unravel_index(np.argmax(np.abs(reproduced)), reproduced.shape)
    assert abs(np.max(np.abs(reproduced))
               -reported['max_moment_relative_error']) < 1e-12
    rows.append({
        'n':n,
        'independently_replayed_rows':len(scan['x_scan']),
        'recorded_vs_replayed_relative_moment_array_max_abs_error':comparison,
        'full_target_max_relative_moment_error':float(np.max(np.abs(reproduced))),
        'finite_domain_max_relative_quadrature_error':float(np.max(np.abs(finite_domain_errors))),
        'finite_domain_omission_max_fraction':float(np.max(lower_omitted)),
        'worst_x':float(scan['x_scan'][new_worst[0]]),
        'worst_flavor':('e','mu')[new_worst[1]],
        'worst_order':int(new_worst[2]),
        'passes_declared_moment_gate_on_all_replayed_rows':bool(np.max(np.abs(reproduced))<=.005),
    })
    print(json.dumps(rows[-1]), flush=True)

inputs = [configuration_path for configuration_path in (
    DOMAIN/'predeclaration.json', DOMAIN/'refinement_predeclaration.json',
    DOMAIN/'source_grid_diagnostic.py', snapshot_path, scan_path,
    producer_result_path)]
receipt = {
    'classification':'independent_public_source_artifact_review',
    'reference_representation':'electron Beta(3,2), muon 2*Beta(3,1)-Beta(4,1); incomplete beta moments',
    'synthetic_snapshot_source_beta_reference_peak_scaled_error':source_error,
    'synthetic_snapshot_state_independent_comoving_entropy_peak_scaled_error':state_error,
    'snapshot_is_trajectory':False,
    'charge_histories_independently_evolved':False,
    'source_callback_identity_peak_scaled_error_max':max_callback_identity_error,
    'phase_rows':rows,
    'scope':'Producer source callback and native weights replayed; no collision execution, transport, production stepper, weak or nuclear evolution',
    'inputs_sha256':{str(p.relative_to(DOMAIN)):sha(p) for p in inputs},
    'reference_module_sha256':sha(OUT/'finite_domain_reference.py'),
    'review_script_sha256':sha(__file__),
}
(OUT/'domain_artifact_independent_review.json').write_text(
    json.dumps(receipt,indent=2,sort_keys=True)+'\n')
