#!/usr/bin/env python3
"""Replay reviewer calculations and independently inspect public peer outputs.

Does not import any upstream or provider module. The continuum script is
executed as a separate diagnostic, and native fixture outputs are read only.
Default execution prints JSON; --output refuses existing paths.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np
from scipy.integrate import quad


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def folder_hashes(folder):
    return {str(p.relative_to(folder)):digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def check_manifest(folder,name):
    manifest=json.loads((folder/name).read_text())
    entries=manifest.get('file_sha256',manifest)
    for path,expected in entries.items():
        member=folder/path
        if not member.is_file() or digest(member)!=expected:
            raise RuntimeError(f'Peer manifest mismatch: {folder.name}/{path}')
    return {'members_checked':len(entries),'all_member_hashes_match':True,'manifest_sha256':digest(folder/name)}


def compare_numeric_tree(a, b, path='root', skip_runtime=False):
    if isinstance(a,dict) and isinstance(b,dict):
        if set(a)!=set(b):
            raise RuntimeError(f'Key mismatch at {path}')
        for key in a:
            if key=='runtime' and skip_runtime:
                continue
            compare_numeric_tree(a[key],b[key],f'{path}.{key}',skip_runtime)
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):
            raise RuntimeError(f'Length mismatch at {path}')
        for i,(x,y) in enumerate(zip(a,b)):
            compare_numeric_tree(x,y,f'{path}[{i}]',skip_runtime)
    elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        if not math.isclose(a,b,rel_tol=2e-12,abs_tol=2e-15):
            raise RuntimeError(f'Numeric mismatch at {path}: {a!r}, {b!r}')
    elif a!=b:
        raise RuntimeError(f'Value mismatch at {path}')


def native_fixture_check(folder):
    receipt=json.loads((folder/'result.json').read_text())
    config=receipt['configuration']
    n=config['rhs_n']
    source=list(csv.DictReader((folder/'preosc_positive_on_0_muonDistribution.csv').open()))
    delta=[float(row['delta_dstate_dx']) for row in csv.DictReader((folder/'delta_positive_on_minus_off.csv').open())]
    state=np.array([float(row['state']) for row in csv.DictReader((folder/'fixed_state.csv').open())])
    vectors={tag:np.array([float(row['dstate_dx']) for row in csv.DictReader((folder/f'rhs_{tag}.csv').open())]) for tag in ('zero_off','zero_on','positive_off','positive_on')}
    if len(source)!=n or len(delta)!=3*n+2:
        raise RuntimeError('Native fixture dimensions disagree')
    if state.shape!=(3*n+2,) or any(vector.shape!=(3*n+2,) for vector in vectors.values()):
        raise RuntimeError('Native state/full RHS dimensions disagree')
    if not np.array_equal(vectors['positive_on']-vectors['positive_off'],np.array(delta)):
        raise RuntimeError('Saved native delta differs from the actual saved on/off vectors')
    if not np.array_equal(vectors['zero_on'],vectors['zero_off']):
        raise RuntimeError('Raw zero-count gate vectors differ')
    branch=config['rhs_native_branching_muon']
    if branch != config['rhs_primary_muon_multiplicity']:
        raise RuntimeError('Native fixture labels must equal the actual primary-muon multiplicity')
    me=receipt['native_me_MeV']
    x=config['rhs_x']
    tau=config['rhs_lifetime_seconds']
    count=config['rhs_llp_count']
    t=config['rhs_t_seconds']
    dt=receipt['runs']['positive_on']['dtdx_seconds']
    if dt!=vectors['positive_on'][-1] or vectors['positive_on'][-1]!=vectors['positive_off'][-1]:
        raise RuntimeError('Same-parent-count Hubble/time derivative differs across native gates')
    if state[-2]!=config['rhs_z'] or state[-1]!=t:
        raise RuntimeError('Saved native fixed temperature/time differs from its configuration')
    q=np.array([float(row['q']) for row in source])
    fd=1/(np.exp(q/config['rhs_z'])+1)
    fd_error=float(np.max(np.abs(state[:-2]-np.tile(fd,3))))
    if fd_error>2e-15:
        raise RuntimeError('Saved native occupations differ from the declared equal-flavor FD fixed state')
    p_mapping_error=max(abs(float(row['p_MeV'])-float(row['q'])*me/x) for row in source)
    if p_mapping_error>2e-13:
        raise RuntimeError('Captured source physical momenta differ from native coordinate mapping')
    # Summing flavors removes the stochastic averaged-mixing map. Source-only
    # occupation change inferred from the independently read native emitter.
    scale=dt*branch*count*math.exp(-t/tau)*(me/x)**3*math.pi**2/tau
    expected=[scale*sum(float(row[key]) for key in ('phi_e','phi_mu','phi_tau'))/float(row['p_MeV'])**2 for row in source]
    actual=[sum(delta[i+flavor*n] for flavor in range(3)) for i in range(n)]
    error=max(abs(a-e) for a,e in zip(actual,expected))
    peak=max(expected)
    if error>2e-12*peak+1e-30:
        raise RuntimeError('Native on/off flavor-summed source amplitude does not match the stated input')
    # Independent mathematical reconstruction of the inspected averaged
    # mixing expressions; no native mixing callable/module is imported.
    s12,s23,s13=math.sqrt(.303),math.sqrt(.572),math.sqrt(.02203)
    c12,c13=math.sqrt(1-s12*s12),math.sqrt(1-s13*s13)
    ds12,ds13=math.sin(2*math.asin(s12)),math.sin(2*math.asin(s13))
    dc12,dc13=math.cos(2*math.acos(c12)),math.cos(2*math.acos(c13))
    th23=math.asin(s23)
    temperature=config['rhs_z']/x*me
    mixed=[]
    for row in source:
        p=float(row['p_MeV'])
        A=8.65785*1.1663787e-11/(80.379e3)**2*p*p*temperature**4
        th12=math.atan2(ds12,dc12+A/7.41e-17)/2
        th13=math.atan2(ds13,dc13+A/2.511e-15)/2
        sa,ca=math.sin(th12),math.cos(th12)
        sb,cb=math.sin(th13),math.cos(th13)
        sc,cc=math.sin(th23),math.cos(th23)
        r12=np.array([[ca,sa,0.],[-sa,ca,0.],[0.,0.,1.]])
        r13=np.array([[cb,0.,sb],[0.,1.,0.],[-sb,0.,cb]])
        r23=np.array([[1.,0.,0.],[0.,cc,sc],[0.,-sc,cc]])
        squared=(r23@r13@r12)**2
        probability=squared@squared.T
        unmixed=scale*np.array([float(row[key]) for key in ('phi_e','phi_mu','phi_tau')])/p**2
        mixed.append(probability@unmixed)
    reconstructed=np.array(mixed).T.reshape(-1)
    mixed_error=float(np.max(np.abs(reconstructed-np.array(delta[:-2]))))
    mixed_peak=float(np.max(np.abs(reconstructed)))
    if mixed_error>2e-12*mixed_peak+1e-30:
        raise RuntimeError('Independent source and averaged-mixing reconstruction disagrees with native RHS delta')
    if not receipt['zero_gate_vectors_bitwise_equal'] or receipt['positive_gate_delta_dtdx']!=0.:
        raise RuntimeError('Native same-state controls do not cancel as expected')
    if receipt['numba_jit_disabled'] or not receipt['native_collision_nopython_signatures']:
        raise RuntimeError('Native fixture lacks compiled collision evidence')
    if delta[-2]==0 or receipt['positive_off_minus_zero_off_dtdx']==0:
        raise RuntimeError('Native photon or parent-density response is absent')
    return {
        'classification':'independent_read_only_local_RHS_fixture_check',
        'actual_primary_muon_multiplicity':branch,'implied_pair_probability':branch/2,
        'source_flavor_sum_peak_abs_error':error,'source_flavor_sum_peak_scaled_error':error/peak,
        'raw_saved_delta_equals_on_minus_off_bitwise':True,'fixed_state_FD_max_abs_error':fd_error,'captured_p_mapping_max_abs_error_MeV':p_mapping_error,
        'all_flavor_mixed_source_peak_abs_error':mixed_error,'all_flavor_mixed_source_peak_scaled_error':mixed_error/mixed_peak,
        'native_Hubble_MeV_inferred_from_time_derivative':6.582e-22/(x*dt),
        'mixing_reconstruction_scope':'Independently transcribed inspected native constants and rotation/mixing mathematics, with measured dtdx and captured unscaled emitter values. Static same-state local reconstruction, not a canonical source export or production stepper.',
        'zero_count_gate_control_bitwise_equal':True,
        'same_positive_count_gate_dtdx_difference':receipt['positive_gate_delta_dtdx'],
        'gate_photon_dzdx_difference':delta[-2],
        'parent_density_off_gate_vs_zero_count_dtdx_difference':receipt['positive_off_minus_zero_off_dtdx'],
        'real_collision_compilation_recorded':True,
        'limits':'Gate changes neutrino injection and parent energy deposition simultaneously, retaining parent density/Hubble in both positive lanes. No stepper, production bridge, evolved history, global conservation, frozen-source normalization or BBN result is certified.',
        'read_files_sha256':{name:digest(folder/name) for name in ('result.json','fixed_state.csv','delta_positive_on_minus_off.csv','preosc_positive_on_0_muonDistribution.csv','rhs_zero_off.csv','rhs_zero_on.csv','rhs_positive_off.csv','rhs_positive_on.csv')},
    }


def mass_shape_check(receipt):
    frozen=receipt['constants']['mmu_frozen_MeV']
    native=receipt['constants']['mmu_native_MeV']
    reference=receipt['native_frozen_mass_mismatch']
    limits={'e':reference['e_density_crossing_energy_MeV'],'mu':frozen/2}
    result={}
    for flavor in ('e','mu'):
        def physical_density(p,mass):
            if p<0 or p>mass/2:
                return 0.
            if flavor=='e':
                return 96*p*p*(1-2*p/mass)/mass**3
            return 48*p*p*(1-4*p/(3*mass))/mass**3
        difference=lambda p:physical_density(p,frozen)-physical_density(p,native)
        edges=sorted(set([0.,limits[flavor],frozen/2,native/2]))
        l1=sum(quad(lambda p:abs(difference(p)),a,b,epsabs=1e-15,epsrel=1e-12)[0] for a,b in zip(edges[:-1],edges[1:]))
        cdf=abs(quad(difference,0.,limits[flavor],epsabs=1e-15,epsrel=1e-12)[0])
        tail=quad(lambda p:physical_density(p,native),frozen/2,native/2,epsabs=1e-15,epsrel=1e-12)[0]
        errors=[abs(l1-reference['full_continuum_normalized_shape_L1'][flavor]),abs(cdf-reference['full_continuum_CDF_max'][flavor]),abs(tail-reference['number_mass_above_frozen_endpoint'][flavor])]
        if max(errors)>5e-13:
            raise RuntimeError('Native/frozen continuum shape analytic result disagrees with independent physical-energy quadrature')
        result[flavor]={'independent_physical_energy_L1':l1,'independent_CDF_max':cdf,'independent_above_frozen_endpoint_number':tail,'max_abs_analytic_quadrature_difference':max(errors)}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nudec-dir',type=Path,required=True)
    parser.add_argument('--primat-dir',type=Path,required=True)
    parser.add_argument('--cards-file',type=Path,required=True)
    parser.add_argument('--coverage-dir',type=Path,required=True)
    parser.add_argument('--source-audit-dir',type=Path,required=True)
    parser.add_argument('--native-rhs-dir',type=Path,required=True,help='Correctly labeled selected native RHS fixture')
    parser.add_argument('--native-probe-dir',type=Path,required=True,help='Entire final native probe dossier to hash')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f'Refusing to overwrite existing output: {args.output}')
    review_dir=Path(__file__).resolve().parent
    before=folder_hashes(review_dir)
    common=['--nudec-dir',str(args.nudec_dir),'--cards-file',str(args.cards_file)]
    result={'classification':'internal_AI_assisted_skeptical_artifact_review','author_date':'2026-10-01 America/Los_Angeles','runtime':{'python':platform.python_version()},'reviewer_replays':{}}
    with tempfile.TemporaryDirectory(prefix='dmde-review-',dir='/tmp') as temporary:
        for script_name,receipt_name in [('independent_domain_review.py','independent_domain_review.json'),('table_proxy_sensitivity.py','table_proxy_sensitivity.json')]:
            command=[sys.executable,str(review_dir/script_name),*common]
            run=subprocess.run(command,capture_output=True,text=True,check=True)
            replay=json.loads(run.stdout)
            baseline=json.loads((review_dir/receipt_name).read_text())
            compare_numeric_tree(replay,baseline,skip_runtime=True)
            output=Path(temporary)/receipt_name
            written=subprocess.run([*command,'--output',str(output)],capture_output=True,text=True,check=True)
            if json.loads(written.stdout)!=json.loads(output.read_text()):
                raise RuntimeError('New output and stdout differ')
            prior=digest(output)
            refused=subprocess.run([*command,'--output',str(output)],capture_output=True,text=True)
            if refused.returncode!=2 or digest(output)!=prior:
                raise RuntimeError('Overwrite refusal did not preserve the prior receipt')
            result['reviewer_replays'][script_name]={'numerically_matches_saved_receipt':True,'replay_runtime':replay['runtime'],'stdout_matches_new_output':True,'overwrite_refusal_exit_code':2,'refused_file_unchanged':True}
        coverage_command=[sys.executable,str(args.coverage_dir/'source_coverage.py'),'--nudec-dir',str(args.nudec_dir),'--primat-dir',str(args.primat_dir)]
        coverage_run=subprocess.run(coverage_command,capture_output=True,text=True,check=True)
        coverage_replay=json.loads(coverage_run.stdout)
        coverage_saved=json.loads((args.coverage_dir/'source_coverage.json').read_text())
        compare_numeric_tree(coverage_replay,coverage_saved,skip_runtime=True)
        optimized=subprocess.run([sys.executable,'-O',str(args.coverage_dir/'source_coverage.py')],capture_output=True,text=True)
        if optimized.returncode!=2 or optimized.stdout:
            raise RuntimeError('Coverage script optimization guard failed')
        result['peer_coverage_replay']={'numerically_and_provenance_matches_saved_receipt':True,'replay_runtime':coverage_replay['runtime'],'optimized_python_rejected_exit_code':2}
    if before!=folder_hashes(review_dir):
        raise RuntimeError('Replay changed the reviewer dossier')
    result['default_and_new_output_replay_leave_reviewer_dossier_unchanged']=True
    result['native_rhs_fixture']=native_fixture_check(args.native_rhs_dir)
    result['native_frozen_mass_shape_crosscheck']=mass_shape_check(json.loads((review_dir/'independent_domain_review.json').read_text()))
    result['peer_manifest_checks']={
        'source_audit':check_manifest(args.source_audit_dir,'AUDIT_ARTIFACT_SHA256.json'),
        'coverage':check_manifest(args.coverage_dir,'ARTIFACT_SHA256.json'),
        'native_canonical_complete':check_manifest(args.native_probe_dir,'artifact_sha256_complete.json'),
        **{f'native/{name}':check_manifest(args.native_probe_dir/name,'artifact_sha256.json') for name in ('results-2026-10-01','results-2026-10-01-corrected-rhs','results-2026-10-01-final-rhs')},
    }
    result['reviewed_peer_files_sha256']={
        'source_audit/'+str(p.relative_to(args.source_audit_dir)):digest(p) for p in sorted(args.source_audit_dir.rglob('*')) if p.is_file()
    }
    result['reviewed_peer_files_sha256'].update({'source_coverage/'+str(p.relative_to(args.coverage_dir)):digest(p) for p in sorted(args.coverage_dir.rglob('*')) if p.is_file()})
    result['reviewed_peer_files_sha256'].update({'native_probe/'+str(p.relative_to(args.native_probe_dir)):digest(p) for p in sorted(args.native_probe_dir.rglob('*')) if p.is_file()})
    result['limits']='Native source execution was performed by the separate probe wrapper. This reviewer reads its outputs and does not run a production transport/weak/BBN solver. Exact derivation and reference-table proxy remain distinct from runtime evidence.'
    rendered=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.output is not None:
        with args.output.open('x') as stream:
            stream.write(rendered)
    print(rendered,end='')


if __name__=='__main__':
    main()
