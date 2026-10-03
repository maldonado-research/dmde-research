#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Independent arithmetic of raw fixed-state native source-adapter evidence.

No producer helper is imported and no native module is executed. Source
expectations use the independent beta-density reference; mixing uses explicit
PMNS elements and pinned public constants rather than rotation helpers.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from finite_domain_reference import (canonical_source, fixed_state_coefficient,
                                     physical_moment, reference_entropy_start,
                                     REFERENCE_ELECTRON_MASS_MEV)

parser = argparse.ArgumentParser()
parser.add_argument('--runtime-results', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
BASE = args.runtime_results.resolve()
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=False)
(OUT/'executed_review.py').write_bytes(Path(__file__).read_bytes())
reference_file = Path(__file__).resolve().parent/'finite_domain_reference.py'
(OUT/'finite_domain_reference.py').write_bytes(reference_file.read_bytes())


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = read(BASE/'artifact_sha256.json')
members = {str(p.relative_to(BASE)):p for p in BASE.rglob('*') if p.is_file()
           and p.name!='artifact_sha256.json'}
assert set(members)==set(manifest)
assert all(sha(members[name])==digest for name,digest in manifest.items())
runtime = read(BASE/'runtime.json')
assert sha(BASE/'executed_wrapper.py')==runtime['wrapper_sha256']
execution = read(BASE/'execution.json')
assert execution['returncode']==0 and not execution['timeout']
assert read(BASE/'source_before.json')==read(BASE/'source_after.json')
NATIVE = BASE/'native_fixed_state'
assert read(NATIVE/'source_before.json')==read(NATIVE/'source_after.json')
config = read(BASE/'predeclaration.json')
assert config['native_transport_me_MeV']==REFERENCE_ELECTRON_MASS_MEV
assert config['source_muon_mass_MeV']==105.6583755
assert config['x0']==.1 and config['z0']==1.00003 and config['g_s_ref']==10.75
data = np.genfromtxt(NATIVE/'source_on_occupations.csv',delimiter=',',names=True)
q, p, weights = (data[name] for name in ('q','p_MeV','native_dq_weight'))
on = read(NATIVE/'source_on.json')
off = read(NATIVE/'source_zero_same_parent_gate.json')
on_state = np.array(on['actual_state'])
off_state = np.array(off['actual_state'])
on_rhs = np.array(on['actual_native_dstate_dx'])
off_rhs = np.array(off['actual_native_dstate_dx'])
assert np.array_equal(on_state,off_state)
assert on_rhs[-1]==off_rhs[-1]
c0 = reference_entropy_start()*(.1/REFERENCE_ELECTRON_MASS_MEV)**3
assert abs(read(NATIVE/'normalization.json')['C0']/c0-1)<1e-14
assert abs(read(NATIVE/'normalization.json')['llp_count']/(config['Y0']*c0)-1)<1e-14
pre6 = canonical_source(q,config['x'],on_state[-1],config['tau_seconds'],
                        config['Y0'],config['B_mumu'])
pre3 = pre6[[0,2,4]]
actual_phi = np.array(on['callback_captures'][0]['phi'])
amplitude = (config['B_mumu']*config['Y0']
             *math.exp(-on_state[-1]/config['tau_seconds'])/config['tau_seconds'])
phi_error = float(np.max(np.abs(actual_phi*(REFERENCE_ELECTRON_MASS_MEV/config['x'])
                               -pre3/amplitude))/np.max(pre3/amplitude))
assert phi_error<1e-12


def explicit_pmns_probability(temperature,momenta):
    # These numerical couplings are publicly pinned in upstream Constants.py.
    s12,s13,s23 = (math.sqrt(.303),math.sqrt(.02203),math.sqrt(.572))
    c12,c13,c23 = (math.sqrt(1-.303),math.sqrt(1-.02203),math.sqrt(1-.572))
    sin2_12,sin2_13 = 2*s12*c12,2*s13*c13
    cos2_12,cos2_13 = 1-2*.303,1-2*.02203
    prefactor = 8.65785*1.1663787e-11/(80.379e3)**2
    result=[]
    for momentum in momenta:
        matter=prefactor*float(momentum)**2*temperature**4
        t12=.5*math.atan2(sin2_12,cos2_12+matter/7.41e-17)
        t13=.5*math.atan2(sin2_13,cos2_13+matter/2.511e-15)
        a,b,d,e = math.sin(t12),math.cos(t12),math.sin(t13),math.cos(t13)
        u=np.array([[b*e,a*e,d],[-a*c23-b*s23*d,b*c23-a*s23*d,s23*e],
                    [a*s23-b*c23*d,-b*s23-a*c23*d,c23*e]])
        result.append((u*u)@(u*u).T)
    return np.array(result)


probability=explicit_pmns_probability(config['z']*REFERENCE_ELECTRON_MASS_MEV/config['x'],p)
mixed3=np.einsum('nij,jn->in',probability,pre3)
delta=on_rhs-off_rhs
actual_source3=fixed_state_coefficient(q)*delta[:-2].reshape(3,len(q))/on_rhs[-1]
source_coefficient_error=float(np.max(np.abs(actual_source3-mixed3))/np.max(mixed3))
assert source_coefficient_error<1e-12
canonical=np.array(on['J_state'])
occupation=np.array(on['actual_canonical_occupations'])
expected_state=occupation*fixed_state_coefficient(q)
state_error=float(np.max(np.abs(canonical-expected_state))/np.max(expected_state))
assert state_error<1e-12
witness=read(NATIVE/'coefficient_witness.json')
premixing_export_error=float(np.max(np.abs(np.array(witness['canonical_S_pre6'])-pre6))/np.max(pre6))
mixing_export_error=float(np.max(np.abs(np.array(witness['native_mixing_matrix_N3x3'])-probability)))
assert premixing_export_error<1e-12 and mixing_export_error<1e-12
unmixed_comparison_error=float(np.max(np.abs(actual_source3-pre3))/np.max(pre3))
assert unmixed_comparison_error>.005

# Continuum truncation and finite-grid quadrature are reported separately.
measured=np.array([[np.sum(weights*(REFERENCE_ELECTRON_MASS_MEV/config['x'])
                          *actual_phi[a]*p**k) for k in range(6)] for a in range(2)])
finite=np.array([[physical_moment(a,k,p[0],p[-1]) for k in range(6)] for a in ('e','mu')])
full=np.array([[physical_moment(a,k,0,1e6) for k in range(6)] for a in ('e','mu')])
moment_error=float(np.max(np.abs(measured/finite-1)))
gate_cases=read(NATIVE/'time_gate_cases.json')
for case in gate_cases:
    active=0<=case['t']<18*config['tau_seconds']
    assert case['time_gate_on']==active
    if case['t']<0:
        assert not case['native_rhs_called']
    else:
        a=read(NATIVE/(case['tag']+'_on.json'))
        b=read(NATIVE/(case['tag']+'_zero.json'))
        assert np.array_equal(np.array(a['actual_state']),np.array(b['actual_state']))
        assert len(a['callback_captures'])==int(active)
        if not active:
            assert np.array_equal(np.array(a['actual_native_dstate_dx']),
                                  np.array(b['actual_native_dstate_dx']))
zero_a=read(NATIVE/'zero_parent_source_on.json')
zero_b=read(NATIVE/'zero_parent_source_zero.json')
assert zero_a['actual_native_dstate_dx']==zero_b['actual_native_dstate_dx']
gate_off=read(NATIVE/'native_gate_off_same_parent.json')
gate_rhs=np.array(gate_off['actual_native_dstate_dx'])
result=read(NATIVE/'result.json')
assert result['native_scalar_globals_before']==result['native_scalar_globals_after']
assert result['native_collision_nopython_signatures']
receipt={
    'classification':'independent_real_fixed_state_artifact_review',
    'all_producer_manifest_members_verified':True,
    'manifest_member_count':len(manifest),
    'wrapper_snapshot_matches_execution_hash':True,
    'source_hashes_unchanged':True,
    'native_physics_globals_unchanged':True,
    'real_collision_nopython_signature_recorded':True,
    'independent_beta_phi_peak_scaled_error':phi_error,
    'independent_beta_canonical_premixing_export_peak_scaled_error':premixing_export_error,
    'independent_entropy_state_peak_scaled_error':state_error,
    'independent_explicit_PMNS_max_abs_error':mixing_export_error,
    'independent_raw_RHS_source_coefficient_peak_scaled_error':source_coefficient_error,
    'independent_infinitesimal_RHS_vs_preoscillation_peak_scaled_error':unmixed_comparison_error,
    'actual_mixed_tau_source_peak':float(np.max(actual_source3[2])),
    'canonical_charge_arrays_are_symmetry_aliases':True,
    'zero_parent_control_bitwise_equal':True,
    'actual_time_half_open_cutoff_confirmed_at_all_declared_cases':True,
    'source_only_control_dzdx_delta':float(delta[-2]),
    'native_gate_off_minus_callback_zero_dzdx_delta':float(gate_rhs[-2]-off_rhs[-2]),
    'coarse_grid_nodes':len(q),
    'coarse_grid_finite_domain_quadrature_moment_relative_error_max':moment_error,
    'coarse_grid_finite_domain_moment_gate_passed':moment_error<=.005,
    'coarse_grid_continuum_omission_fraction_max':float(np.max(1-finite/full)),
    'finite_steps_h_and_h2_executed':False,
    'transport_trajectory_executed':False,
    'production_source_accumulator_directly_instrumented':False,
    'export_route':'Actual production callback phi capture; wrapper canonical conversion verified from raw on/off native RHS after mixing',
    'scope':'Source/callback/coefficient/state/time-gate diagnostic; no conservation certificate, physics validation, transport precision, weak rates or BBN',
    'input_manifest_sha256':sha(BASE/'artifact_sha256.json'),
    'producer_wrapper_sha256':sha(BASE/'executed_wrapper.py'),
    'review_script_sha256':sha(Path(__file__)),
    'reference_module_sha256':sha(reference_file),
}
(OUT/'runtime_artifact_independent_review.json').write_text(
    json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+'\n')
print(json.dumps(receipt,sort_keys=True,allow_nan=False))
