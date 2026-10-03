#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Separately labeled pressure-consistent QED COMPONENT reference.

This authored helper uses native P2/I/dIdz and the native QED quadrature,
with the exact analytic P2 derivative and paper equation 2.53 for rho3.
It does not replace native callables/globals or define a repaired full EOS.
No System_Nudec, trajectory or cosmological observable is evaluated.

Distributed under GNU GPL version 3; see COPYING. The mathematical
equations are independently transcribed; the imported upstream package
retains its own provenance and license. Preserve the original negative
receipts when using this separately labeled reference.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import integrate

from conservation_review import complex_partial, read_json, sha256, snapshot
from qed_identity_review import DECLARATION, five_point


def pressure_consistent_components(x, z, constants, grid, native_qed):
    """Return isolated corrected QED components on the stated native grid.

    The caller supplies the imported official modules. No module symbol or
    global is modified. Complex x/z inputs are supported for derivative
    checks. This function is a reviewable component reference only.
    """
    q = np.linspace(grid.yQED_min, grid.yQED_max, grid.n_QED)
    energy = np.sqrt(q*q+x*x)
    f = 1.0/(np.exp(energy/z)+1.0)
    a = integrate.simpson(2*q*q/energy*f, x=q)
    a_z = integrate.simpson(2*q*q/(z*z)*f*(1-f), x=q)
    derivative_p2 = (-constants.e**2*z*a/(6*math.pi**2)
                     -constants.e**2*z*z*a_z/(12*math.pi**2)
                     -constants.e**2*a*a_z/(4*math.pi**4))
    p2 = native_qed.P_2(x,z)
    rho2 = -p2+z*derivative_p2
    integral = native_qed.I(x,z)
    integral_z = native_qed.dIdz(x,z)
    p3 = constants.e**3*z*integral**1.5/(12*math.pi**4)
    rho3 = constants.e**3*z*z*np.sqrt(integral)*integral_z/(8*math.pi**4)
    return {"P2_native":p2, "dP2dz_pressure_consistent":derivative_p2,
            "rho2_pressure_consistent":rho2,
            "P3_paper":p3, "rho3_pressure_consistent":rho3}


def run(args):
    source = args.source.resolve()
    before = snapshot(source)
    sys.path.insert(0,str(source))
    import Constants as constants
    import Momentum_Grid as grid
    import Thermodynamics.Thermal_QED_corrections as native_qed
    grid.setupGrid(40.0,301,0.01)
    rows=[]
    for n in DECLARATION["native_QED_n"]:
        grid.n_QED=n
        grid.dyQED=(grid.yQED_max-grid.yQED_min)/(n-1)
        for x,z in DECLARATION["states_x_z"]:
            component=lambda xx,zz: pressure_consistent_components(xx,zz,constants,grid,native_qed)
            corrected=component(x,z)
            native_rho2,native_rho3=native_qed.Thermal_QED_corrections_to_energy_density(x,z)
            actual_p2z=complex_partial(native_qed.P_2,x,z,"z")
            actual_p3z=complex_partial(lambda xx,zz:component(xx,zz)["P3_paper"],x,z,"z")
            p2_identity=z*actual_p2z-corrected["P2_native"]
            p3_identity=z*actual_p3z-corrected["P3_paper"]
            finite_checks=[]
            for relative in DECLARATION["finite_difference_relative_steps"]:
                h=z*relative
                p2z_fd=five_point(native_qed.P_2,x,z,h)
                p3z_fd=five_point(lambda xx,zz:component(xx,zz)["P3_paper"],x,z,h)
                finite_checks.append({"h_over_z":relative,
                    "dP2dz_five_point":float(p2z_fd),
                    "rho2_reference_minus_finite_diff_pressure_identity":float(corrected["rho2_pressure_consistent"]-(z*p2z_fd-corrected["P2_native"])),
                    "dP3dz_five_point":float(p3z_fd),
                    "rho3_reference_minus_finite_diff_pressure_identity":float(corrected["rho3_pressure_consistent"]-(z*p3z_fd-corrected["P3_paper"]))})
            delta2=native_rho2-corrected["rho2_pressure_consistent"]
            delta3=native_rho3-corrected["rho3_pressure_consistent"]
            photon=math.pi**2*z**4/15
            rows.append({"x":x,"z":z,"native_QED_n":n,
                "corrected_component_reference":{key:float(value) for key,value in corrected.items()},
                "native_components_preserved":{"dP2dz":float(native_qed.dP_2dz(x,z)),"rho2":float(native_rho2),"rho3":float(native_rho3)},
                "native_minus_reference_rho2":float(delta2),"native_minus_reference_rho3":float(delta3),
                "native_minus_reference_rho2_over_reference":float(delta2/corrected["rho2_pressure_consistent"]),
                "native_minus_reference_rho3_over_reference":float(delta3/corrected["rho3_pressure_consistent"]),
                "native_minus_reference_rho2_over_photon":float(delta2/photon),
                "native_minus_reference_rho3_over_photon":float(delta3/photon),
                "reference_dP2dz_minus_complex_step_actual_P2":float(corrected["dP2dz_pressure_consistent"]-actual_p2z),
                "rho2_reference_minus_complex_step_pressure_identity":float(corrected["rho2_pressure_consistent"]-p2_identity),
                "rho3_reference_minus_complex_step_pressure_identity":float(corrected["rho3_pressure_consistent"]-p3_identity),
                "finite_difference_checks":finite_checks})
    grid.n_QED=81
    grid.dyQED=(grid.yQED_max-grid.yQED_min)/80
    after=snapshot(source)
    if before!=after:
        raise RuntimeError("Official source changed during component reference check")
    original=read_json(Path(__file__).with_name("qed_identity_review.json"))
    outcome={"scope":"Isolated QED component correction reference, not a replaced native EOS or trajectory",
        "license":"GPL-3.0-only", "component_reference_callable":"qed_component_reference.pressure_consistent_components",
        "native_symbols_modified":False,"native_constants_modified":False,
        "native_QED_quadrature_refinement":"Explicit temporary n_QED81/161/321, same endpoints, native functions unchanged, default restored",
        "declaration":DECLARATION,
        "runtime":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"executable":sys.executable},
        "timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "script_sha256":sha256(__file__),"source_snapshot":before,"source_unchanged":True,
        "original_negative_receipt_sha256":sha256(Path(__file__).with_name("qed_identity_review.json")),
        "primary_reference":original["primary_reference"],
        "reference_derivation":"Actual analytic derivative of native P2 (pi^4 in final denominator); arxiv2210.10307 eq2.53 cubic energy z^2 after comoving conversion; native fixed-grid I,dIdz retained",
        "not_validated":"Full EOS, derivative heat-capacity consistency on finite grid, native Hubble or transport trajectory, weak rates, BBN, observational effects",
        "observations":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as file:
        json.dump(outcome,file,indent=2,sort_keys=True,allow_nan=False)
        file.write("\n")
    print(json.dumps({"output":str(args.output),"source_unchanged":True,
        "default_n81":[r for r in rows if r["native_QED_n"]==81]},indent=2,allow_nan=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=Path("/workspace/shared/dmde-upstream/nudec"))
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args())
