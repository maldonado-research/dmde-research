#!/usr/bin/env python3
"""Independent arithmetic review of public runtime adapter receipts.

This imports neither the runtime adapter, native physics modules nor provider
validators. It performs no new native RHS call, trajectory or blind analysis.
Expected Michel arrays and scalar mixing rotations are independently written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def csv(path):
    return np.genfromtxt(path,delimiter=",",names=True)


def matrix(temperature,p):
    # Public pinned Constants.py numbers, without importing a native module.
    gf, mw = 1.1663787e-11, 80.379e3
    matter = 8.65785*gf/mw**2*p*p*temperature**4
    sin12, sin23, sin13 = math.sqrt(.303), math.sqrt(.572), math.sqrt(.02203)
    ds12 = math.sin(2*math.asin(sin12))
    ds13 = math.sin(2*math.asin(sin13))
    dc12 = math.cos(2*math.acos(sin12))
    dc13 = math.cos(2*math.acos(sin13))
    theta12=.5*math.atan2(ds12,dc12+matter/7.41e-17)
    theta13=.5*math.atan2(ds13,dc13+matter/2.511e-15)
    theta23=math.asin(sin23)
    c12,s12=math.cos(theta12),math.sin(theta12)
    c13,s13=math.cos(theta13),math.sin(theta13)
    c23,s23=math.cos(theta23),math.sin(theta23)
    # Explicit PMNS entries, independent of the producer's matrix product.
    u=np.array([[c12*c13,s12*c13,s13],
        [-s12*c23-c12*s23*s13,c12*c23-s12*s23*s13,s23*c13],
        [s12*s23-c12*c23*s13,-c12*s23-s12*c23*s13,c23*c13]])
    probability=u*u
    return probability@probability.T


def main(args):
    bundle=args.bundle.resolve()
    final=bundle/"results-serialization-fix"
    first=bundle/"results-first"
    fixture=final/"native_fixed_state"
    declaration=read(final/"predeclaration.json")
    normalization=read(fixture/"normalization.json")
    d=declaration
    me,mmu=d["native_transport_me_MeV"],d["source_muon_mass_MeV"]
    x,z=d["x"],d["z"]
    tref=d["z0"]*me/d["x0"]
    s0=2*math.pi**2/45*d["g_s_ref"]*tref**3
    c0=s0*(d["x0"]/me)**3
    normalization_expected={"T_ref_MeV":tref,"s0_MeV3":s0,"C0":c0,
        "llp_count":d["Y0"]*c0,"s_ref_fixture_MeV3":s0*(d["x0"]/x)**3}
    state_on=read(fixture/"source_on.json")
    state_off=read(fixture/"source_zero_same_parent_gate.json")
    raw_on=np.array(state_on["actual_native_dstate_dx"])
    raw_off=np.array(state_off["actual_native_dstate_dx"])
    delta=raw_on-raw_off
    occupation=csv(fixture/"source_on_occupations.csv")
    q=occupation["q"]
    p=q*me/x
    n=len(q)
    u=2*p/mmu
    support=(u>=0)&(u<=1)
    phi=np.zeros((3,n))
    phi[0,support]=2/mmu*12*u[support]**2*(1-u[support])
    phi[1,support]=2/mmu*2*u[support]**2*(3-2*u[support])
    capture=state_on["callback_captures"]
    captured=np.array(capture[0]["phi"])
    pre=d["B_mumu"]*d["Y0"]*math.exp(-d["state_t_seconds"]/d["tau_seconds"])/d["tau_seconds"]*(me/x)*phi
    mixing=np.array([matrix(z*me/x,float(pp)) for pp in p])
    mixed=np.einsum("nij,jn->in",mixing,pre)
    actual=q*q/(2*math.pi**2*c0)*delta[:-2].reshape(3,n)/raw_on[-1]
    source_csv=csv(fixture/"canonical_sources.csv")
    saved_pre=np.array([source_csv["S_pre_"+a] for a in ("nue","numu","nutau")])
    saved_actual=np.array([source_csv["actual_native_dJdt_source_"+a] for a in ("nue","numu","nutau")])
    saved_j=np.array([occupation["J_"+a] for a in ("nue","nuebar","numu","numubar","nutau","nutaubar")])
    saved_f=np.array([occupation["f_"+a] for a in ("nue","nuebar","numu","numubar","nutau","nutaubar")])
    normfactor=q*q/(2*math.pi**2*c0)
    coefficient_peak=float(np.max(abs(actual-mixed))/np.max(abs(mixed)))
    frozen_peak=float(np.max(abs(actual-pre))/np.max(abs(pre)))
    checks={
        "normalization_values_match_independent_reference": all(abs(normalization[k]/v-1)<1e-15 for k,v in normalization_expected.items()),
        "source_input_states_bitwise_equal": np.array_equal(state_on["actual_state"],state_off["actual_state"]),
        "physical_momentum_saved_conversion_matches": bool(np.array_equal(occupation["p_MeV"],p)),
        "callback_count_one_in_main_source_lane":len(capture)==1,
        "captured_callback_michel_peak_error_below_1e_minus14":float(np.max(abs(captured-phi))/np.max(abs(phi)))<1e-14,
        "captured_callback_momenta_equal_actual_grid":np.array_equal(capture[0]["momenta_MeV"],p),
        "state_to_yield_mapping_peak_error_below_1e_minus14":float(np.max(abs(saved_j-saved_f*normfactor))/np.max(abs(saved_j)))<1e-14,
        "canonical_pre_source_matches_independent_michel_formula":float(np.max(abs(saved_pre-pre))/np.max(abs(pre)))<1e-14,
        "canonical_actual_source_matches_actual_rhs_delta":np.array_equal(saved_actual,actual),
        "actual_consumption_mixed_coefficient_error_below_1e_minus10":coefficient_peak<1e-10,
        "preoscillation_literal_infinitesimal_comparison_fails":frozen_peak>d["frozen_full_stepper_source_relative_ceiling"],
        "preoscillation_tau_exactly_zero_actual_tau_positive":np.all(pre[2]==0) and np.max(actual[2])>0,
        "same_parent_source_toggle_time_derivative_bitwise_equal":raw_on[-1]==raw_off[-1],
    }
    gate_checks=[]
    for record in read(fixture/"time_gate_cases.json"):
        expected_gate=0<=record["t"]<18*d["tau_seconds"]
        row={"tag":record["tag"],"actual_time_s":record["t"],"expected_half_open_gate":expected_gate,
             "recorded_gate_matches":record["time_gate_on"]==expected_gate}
        if record["t"]<0:
            row.update({"negative_rejected_without_native_rhs":not record["native_rhs_called"] and record["negative_time_interface_rejected"]})
        else:
            on=read(fixture/(record["tag"]+"_on.json"))
            off=read(fixture/(record["tag"]+"_zero.json"))
            r1=np.array(on["actual_native_dstate_dx"])
            r0=np.array(off["actual_native_dstate_dx"])
            row.update({"captured_callback_count":len(on["callback_captures"]),
                "callback_count_matches_gate":len(on["callback_captures"])==int(expected_gate),
                "off_gate_vectors_bitwise_equal":True if expected_gate else bool(np.array_equal(r1,r0)),
                "active_source_changes_neutrino_vector":True if not expected_gate else bool(np.max(abs((r1-r0)[:-2]))>0)})
        gate_checks.append(row)
    checks["actual_time_gate_raw_cases_pass"]=all(all(v for k,v in r.items() if k in ("recorded_gate_matches","negative_rejected_without_native_rhs","callback_count_matches_gate","off_gate_vectors_bitwise_equal","active_source_changes_neutrino_vector")) for r in gate_checks)
    zero_on=read(fixture/"zero_parent_source_on.json")
    zero_off=read(fixture/"zero_parent_source_zero.json")
    checks["zero_parent_source_toggle_vectors_bitwise_equal"]=np.array_equal(zero_on["actual_native_dstate_dx"],zero_off["actual_native_dstate_dx"])
    manifests={}
    for tag,path in [("first",first),("final",final)]:
        manifest=read(path/"artifact_sha256.json")
        mismatches=[rel for rel,want in manifest.items() if not (path/rel).exists() or sha(path/rel)!=want]
        manifests[tag]={"manifest_sha256":sha(path/"artifact_sha256.json"),"member_count":len(manifest),"mismatches":mismatches}
    checks["all_recorded_input_artifact_hashes_match"]=all(not r["mismatches"] for r in manifests.values())
    native_snapshots=[read(final/name) for name in ("source_before.json","source_after.json")]
    native_snapshots.extend(read(fixture/name) for name in ("source_before.json","source_after.json"))
    checks["final_worker_and_supervisor_native_snapshots_identical"]=all(s==native_snapshots[0] for s in native_snapshots)
    source=args.source.resolve()
    current_status=subprocess.check_output(["git","--no-optional-locks","-C",str(source),"status","--porcelain=v1","--untracked-files=all"],text=True).strip()
    current_head=subprocess.check_output(["git","--no-optional-locks","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    native_hashes=native_snapshots[0]["tracked_file_sha256"]
    checks["saved_native_hashes_match_current_pinned_clean_source"]=(current_head==d["upstream_commit"] and not current_status and all(sha(source/path)==digest for path,digest in native_hashes.items()))
    checks["current_wrapper_matches_final_executed_and_predeclared_hash"]=(sha(bundle/"source_adapter_diagnostic.py")==sha(final/"executed_wrapper.py")==read(bundle/"predeclared-serialization-fix"/"wrapper_identity.json")["sha256"])
    checks["first_and_final_scientific_predeclaration_equal"]=(read(first/"predeclaration.json")==declaration)
    first_result=first/"native_fixed_state"/"result.json"
    first_result_parses=True
    try:
        read(first_result)
    except json.JSONDecodeError:
        first_result_parses=False
    outcome={"scope":"Independent raw-receipt and source review; no adapter/native physics/validator import, new RHS or trajectory",
        "runtime":{"python":platform.python_version(),"numpy":np.__version__},
        "input_bundle":str(bundle),"final_lane":"results-serialization-fix",
        "script_sha256":sha(__file__),"checks":{k:bool(v) for k,v in checks.items()},
        "all_required_local_review_checks_passed":bool(all(checks.values())),
        "independent_normalization":normalization_expected,
        "independent_source_consumption":{"mixed_coefficient_peak_relative_error":coefficient_peak,
            "literal_preoscillation_peak_relative_error":frozen_peak,"threshold":d["frozen_full_stepper_source_relative_ceiling"],
            "pre_tau_peak":float(np.max(pre[2])),"actual_mixed_tau_peak":float(np.max(actual[2])),
            "source_only_delta_dzdx":float(delta[-2]),"source_only_delta_dtdx":float(delta[-1]),
            "native_dt_dx_measured_seconds":float(raw_on[-1]),
            "flavor_sum_peak_relative_error":float(np.max(abs(actual.sum(axis=0)-pre.sum(axis=0)))/np.max(abs(pre)))},
        "gate_raw_case_review":gate_checks,"input_artifact_manifest_review":manifests,
        "preserved_first_failure":{"execution":read(first/"execution.json"),"partial_result_JSON_parseable":first_result_parses,
            "partial_result_size_bytes":first_result.stat().st_size,"stderr_sha256":sha(first/"stderr.log"),
            "scientific_state_and_rhs_csv_same_first_final":all(sha(first/"native_fixed_state"/name)==sha(fixture/name) for name in ("source_on_rhs.csv","source_zero_same_parent_gate_rhs.csv","canonical_sources.csv","source_only_delta.csv"))},
        "reviewed_source_hashes":{"runtime_wrapper":sha(bundle/"source_adapter_diagnostic.py"),"final_executed_wrapper":sha(final/"executed_wrapper.py"),"first_executed_wrapper":sha(first/"executed_wrapper.py"),
            "native_upstream_head":current_head,"native_upstream_tracked_sha256":native_hashes,
            "runtime_README":sha(bundle/"README.md"),"CLI_receipt":sha(bundle/"cli-checks"/"result.json")},
        "important_limits":["Captured physical callback is actual; pre-mixing native df_nudx accumulator is not directly instrumented",
            "Canonical pre-source multiplies captured phi by independently verified adapter coefficient; it is not a direct accumulator export",
            "Actual consumption witness is paired fixed-state post-mixing RHS, conditional on measured native dt/dx and native charge symmetry",
            "Literal per-flavor infinitesimal unsplit comparison fails; no h/h2 production-stepper gate was executed",
            "N65 is coarse and no continuum source moments or thermal/collision convergence is certified",
            "Preserved actual serialization failure is not a controlled native failure or timeout; general failure branches reviewed in source only",
            "Native QED defects and continuing exponential parent after cutoff remain; no closed energy trajectory claim"]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(outcome,handle,indent=2,sort_keys=True,allow_nan=False)
        handle.write("\n")
    print(json.dumps({"output":str(args.output),"all_required_local_review_checks_passed":all(checks.values()),
        "independent_source_consumption":outcome["independent_source_consumption"],"preserved_first_partial_JSON_parseable":first_result_parses,
        "failed_checks":[k for k,v in checks.items() if not v]},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle",type=Path,default=Path("/workspace/shared/dmde-adapter-runtime"))
    parser.add_argument("--source",type=Path,default=Path("/workspace/shared/dmde-upstream/nudec"))
    parser.add_argument("--output",type=Path,required=True)
    main(parser.parse_args())
