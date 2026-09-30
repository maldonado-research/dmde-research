#!/usr/bin/env python3
"""Deep, source-frozen validator for the two DMDE spectral payloads.

This validates bytes, schemas, grids, analytic source formulas, energy closure,
and the charged-pion firewall. It does not score or unblind either card.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np

REQ_ARRAYS = {
    "card_id", "t_s", "y_t_over_tau", "x", "E_MeV", "Fe", "Fmu",
    "A_t", "Q_EM_over_s", "Q_nu_over_s", "Q_pi_charged_over_s"
}

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1<<20), b""):
            h.update(block)
    return h.hexdigest()

def trapz(y, x):
    return float(np.trapezoid(y, x))

def relmax(actual, expected, floor=1e-300):
    actual=np.asarray(actual,float); expected=np.asarray(expected,float)
    denom=np.maximum(np.abs(expected), floor)
    return float(np.max(np.abs(actual-expected)/denom))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default=".")
    ap.add_argument("--out-csv", default="DMDE_v0920_deep_payload_validation.csv")
    ap.add_argument("--out-json", default="DMDE_v0920_deep_payload_validation.json")
    ap.add_argument("--rtol-formula", type=float, default=2e-12)
    ap.add_argument("--rtol-integral", type=float, default=2e-5)
    ap.add_argument("--rtol-michel-hierarchy", type=float, default=2.5e-5)
    args=ap.parse_args()
    base=Path(args.base)
    cards=json.loads((base/"tables"/"DMDE_v099_blind_spectral_source_cards.json").read_text())
    with (base/"tables"/"DMDE_v099_blind_payload_manifest.csv").open(newline="", encoding="utf-8") as handle:
        manifest_rows=list(csv.DictReader(handle))
        manifest={r["blind_id"]:r for r in manifest_rows}
    with (base/"tables"/"DMDE_v0920_expected_source_identities.csv").open(newline="", encoding="utf-8") as handle:
        identity_rows=list(csv.DictReader(handle))
        identities={r["blind_id"]:r for r in identity_rows}
    document_hashes={
        "source_card_json_sha256": sha256_file(base/"tables"/"DMDE_v099_blind_spectral_source_cards.json"),
        "payload_manifest_sha256": sha256_file(base/"tables"/"DMDE_v099_blind_payload_manifest.csv"),
        "payload_schema_document_sha256": sha256_file(base/"docs"/"DMDE_v099_PAYLOAD_SCHEMA.json"),
    }
    all_issues=[]
    card_ids=[str(c.get("blind_id", "")) for c in cards]
    manifest_ids=[str(r.get("blind_id", "")) for r in manifest_rows]
    identity_ids=[str(r.get("blind_id", "")) for r in identity_rows]
    locked_ids={"DMDE-SPEC-V099-4Q7N", "DMDE-SPEC-V099-8M2K"}
    for label, values in (("source cards", card_ids), ("payload manifest", manifest_ids), ("identity table", identity_ids)):
        if len(values) != 2 or len(set(values)) != len(values) or set(values) != locked_ids:
            all_issues.append(f"{label}: must contain exactly the two unique frozen blind IDs")
    rows=[]
    for c in cards:
        bid=c["blind_id"]
        issues=[]
        m=manifest.get(bid)
        identity=identities.get(bid)
        pf=base/"payloads"/(m["payload_file"] if m else f"{bid}_spectral_payload_v099.npz")
        row={"blind_id":bid,"status":"FAIL","issues":""}
        if m is None:
            issues.append("missing manifest row")
        if identity is None:
            issues.append("missing frozen identity row")
        else:
            for key, actual in document_hashes.items():
                row[f"{key}_expected"]=identity.get(key,"")
                row[f"{key}_actual"]=actual
                if identity.get(key) != actual:
                    issues.append(f"{key} mismatch")
            exact_pairs=(
                ("source_card_version", c.get("schema_version"), identity.get("source_card_version")),
                ("source_payload_schema", c.get("schema_version_v098_payload"), identity.get("source_payload_schema")),
            )
            for label, actual, expected in exact_pairs:
                if str(actual) != str(expected):
                    issues.append(f"{label} mismatch")
            for key in ("mass_MeV","tau_s","Y0","epsilon","B_mumu","B_ee_plus_EMlike_neutral_effective","f_EM_integrated","f_nu_integrated","m_mu_MeV"):
                try:
                    if not math.isclose(float(c[key]), float(identity[key]), rel_tol=2e-15, abs_tol=0.0):
                        issues.append(f"frozen card {key} mismatch")
                except (KeyError, TypeError, ValueError):
                    issues.append(f"frozen card {key} invalid")
        if not pf.exists():
            issues.append(f"missing payload {pf.name}")
            row["issues"]="; ".join(issues); rows.append(row); all_issues.extend(f"{bid}: {x}" for x in issues); continue
        actual_hash=sha256_file(pf)
        expected_hash=m.get("sha256","") if m else ""
        row.update({"payload_file":pf.name,"sha256_expected":expected_hash,"sha256_actual":actual_hash,"sha256_match":actual_hash==expected_hash})
        if actual_hash != expected_hash: issues.append("sha256 mismatch")
        if identity is not None and actual_hash != identity.get("source_payload_sha256"):
            issues.append("payload hash disagrees with frozen identity table")
        try:
            z=np.load(pf, allow_pickle=False)
        except Exception as exc:
            issues.append(f"npz load error: {exc}")
            row["issues"]="; ".join(issues); rows.append(row); all_issues.extend(f"{bid}: {x}" for x in issues); continue
        missing=sorted(REQ_ARRAYS-set(z.files)); extra=sorted(set(z.files)-REQ_ARRAYS)
        row["required_arrays_present"]=not missing
        row["unexpected_arrays"]="|".join(extra)
        if missing: issues.append("missing arrays: "+",".join(missing))
        if missing:
            z.close()
            row["issues"]="; ".join(issues); rows.append(row); all_issues.extend(f"{bid}: {x}" for x in issues); continue
        card_id=str(z["card_id"])
        t=np.asarray(z["t_s"],float); y=np.asarray(z["y_t_over_tau"],float)
        x=np.asarray(z["x"],float); E=np.asarray(z["E_MeV"],float)
        Fe=np.asarray(z["Fe"],float); Fmu=np.asarray(z["Fmu"],float)
        A=np.asarray(z["A_t"],float); Qe=np.asarray(z["Q_EM_over_s"],float)
        Qn=np.asarray(z["Q_nu_over_s"],float); Qpi=np.asarray(z["Q_pi_charged_over_s"],float)
        arrays=[t,y,x,E,Fe,Fmu,A,Qe,Qn,Qpi]
        z.close()
        finite=all(np.all(np.isfinite(a)) for a in arrays)
        nonnegative=all(np.all(a>=0) for a in [t,y,x,E,Fe,Fmu,A,Qe,Qn,Qpi])
        Nt=int(m["Nt"]); Nx=int(m["Nx"])
        shapes_ok=(t.shape==y.shape==A.shape==Qe.shape==Qn.shape==Qpi.shape==(Nt,) and x.shape==E.shape==Fe.shape==Fmu.shape==(Nx,))
        t_mono=bool(np.all(np.diff(t)>0)); x_mono=bool(np.all(np.diff(x)>0))
        row.update({"card_id":card_id,"card_id_match":card_id==bid,"finite":finite,"nonnegative":nonnegative,"shapes_match_manifest":shapes_ok,"t_strictly_increasing":t_mono,"x_strictly_increasing":x_mono})
        if card_id != bid: issues.append("card_id mismatch")
        if not finite: issues.append("non-finite array value")
        if not nonnegative: issues.append("negative array value")
        if not shapes_ok: issues.append("array shape mismatch")
        if not t_mono or not x_mono: issues.append("non-monotone grid")
        tau=float(c["tau_s"]); Y0=float(c["Y0"]); B=float(c["B_mumu"])
        mass=float(c["mass_MeV"]); mmu=float(c["m_mu_MeV"])
        fEM=float(c["f_EM_integrated"]); fnu=float(c["f_nu_integrated"])
        expected_y=t/tau
        expected_E=0.5*mmu*x
        expected_Fe=12*x*x*(1-x)
        expected_Fmu=2*x*x*(3-2*x)
        decay=Y0*np.exp(-t/tau)/tau
        expected_A=B*decay
        expected_Qe=fEM*mass*decay
        expected_Qn=fnu*mass*decay
        y_err=float(np.max(np.abs(y-expected_y)))
        E_err=float(np.max(np.abs(E-expected_E)))
        Fe_err=float(np.max(np.abs(Fe-expected_Fe)))
        Fmu_err=float(np.max(np.abs(Fmu-expected_Fmu)))
        A_rel=relmax(A,expected_A); Qe_rel=relmax(Qe,expected_Qe); Qn_rel=relmax(Qn,expected_Qn)
        qpi_max=float(np.max(np.abs(Qpi)))
        int_Fe=trapz(Fe,x); int_Fmu=trapz(Fmu,x)
        mean_x_Fe=trapz(x*Fe,x)/int_Fe; mean_x_Fmu=trapz(x*Fmu,x)/int_Fmu
        michel_moment_relerrs={}
        for k in range(6):
            exact_e=12/((k+3)*(k+4))
            exact_mu=2*(k+6)/((k+3)*(k+4))
            michel_moment_relerrs[f"Fe_k{k}_relerr"]=trapz((x**k)*Fe,x)/exact_e-1
            michel_moment_relerrs[f"Fmu_k{k}_relerr"]=trapz((x**k)*Fmu,x)/exact_mu-1
        spec_Qn=A*(2*trapz(E*Fe,x)+2*trapz(E*Fmu,x))
        spec_Qn_rel=relmax(Qn,spec_Qn)
        tail=math.exp(-float(y[-1]))
        decay_fraction=1-tail
        I_EM=trapz(Qe,t); I_nu=trapz(Qn,t); I_pi=trapz(Qpi,t)
        I_EM_expected=fEM*mass*Y0*decay_fraction
        I_nu_expected=fnu*mass*Y0*decay_fraction
        I_EM_rel=abs(I_EM-I_EM_expected)/I_EM_expected
        I_nu_rel=abs(I_nu-I_nu_expected)/I_nu_expected
        row.update({
            "y_t_over_tau_max_abs_error":y_err,"E_formula_max_abs_error_MeV":E_err,
            "Fe_formula_max_abs_error":Fe_err,"Fmu_formula_max_abs_error":Fmu_err,
            "A_t_formula_max_rel_error":A_rel,"Q_EM_formula_max_rel_error":Qe_rel,
            "Q_nu_formula_max_rel_error":Qn_rel,"Q_pi_max_abs":qpi_max,
            "int_Fe_dx":int_Fe,"int_Fmu_dx":int_Fmu,"mean_x_Fe":mean_x_Fe,"mean_x_Fmu":mean_x_Fmu,
            **michel_moment_relerrs,
            "instantaneous_Qnu_spectral_max_rel_error":spec_Qn_rel,"f_EM_plus_f_nu_minus_1":fEM+fnu-1,
            "tail_fraction_beyond_grid":tail,"I_EM_MeV":I_EM,"I_nu_MeV":I_nu,"I_pi_MeV":I_pi,
            "I_EM_truncated_rel_error":I_EM_rel,"I_nu_truncated_rel_error":I_nu_rel,
            "t_max_s":float(t[-1]),"x_min":float(x[0]),"x_max":float(x[-1])
        })
        if y_err>1e-12: issues.append("t/tau grid formula mismatch")
        if E_err>1e-12: issues.append("energy grid formula mismatch")
        if Fe_err>1e-12 or Fmu_err>1e-12: issues.append("Michel formula mismatch")
        if max(A_rel,Qe_rel,Qn_rel)>args.rtol_formula: issues.append("source time-law mismatch")
        if qpi_max!=0 or I_pi!=0: issues.append("charged-pion source nonzero")
        if abs(int_Fe-1)>args.rtol_integral or abs(int_Fmu-1)>args.rtol_integral: issues.append("Michel normalization outside grid tolerance")
        if abs(mean_x_Fe-0.6)>args.rtol_integral or abs(mean_x_Fmu-0.7)>args.rtol_integral: issues.append("Michel moment outside grid tolerance")
        if any(abs(value)>args.rtol_michel_hierarchy for value in michel_moment_relerrs.values()): issues.append("Michel k=0..5 hierarchy outside grid tolerance")
        if spec_Qn_rel>1e-5: issues.append("spectral neutrino-energy closure mismatch")
        if abs(fEM+fnu-1)>1e-14: issues.append("integrated energy fractions do not sum to one")
        if I_EM_rel>args.rtol_integral or I_nu_rel>args.rtol_integral: issues.append("truncated energy integral mismatch")
        if abs(float(t[-1])-float(m["t_max_s"]))>1e-9 or abs(float(x[0])-float(m["x_min"]))>1e-15 or abs(float(x[-1])-float(m["x_max"]))>1e-15:
            issues.append("manifest grid endpoint mismatch")
        row["status"]="PASS" if not issues else "FAIL"
        row["issues"]="; ".join(issues)
        rows.append(row); all_issues.extend(f"{bid}: {x}" for x in issues)
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with Path(args.out_csv).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary={"schema":"DMDE-v0.9.20-deep-payload-validation","payload_count":len(rows),"pass_count":sum(r.get("status")=="PASS" for r in rows),"status":"PASS" if rows and not all_issues else "FAIL","issues":all_issues,"rows":rows}
    Path(args.out_json).write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    if all_issues or not rows:
        print("DEEP VALIDATION FAILED")
        for issue in all_issues: print(issue)
        raise SystemExit(1)
    print(f"DEEP VALIDATION PASSED: {len(rows)} payloads")
if __name__=="__main__": main()
