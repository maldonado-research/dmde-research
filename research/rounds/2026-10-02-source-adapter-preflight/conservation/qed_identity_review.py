#!/usr/bin/env python3
"""Predeclared native QED pressure/energy identity check; no solver execution.

The default native 81-point QED grid is retained as the primary observation.
Two declared grid refinements at the same endpoints test quadrature effects.
Neither the wrong native derivative nor native rho3 is overwritten.
"""
from __future__ import annotations

import argparse
import datetime
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

from conservation_review import (
    complex_partial, reference_plasma, sha256, snapshot,
)

DECLARATION = {
    "states_x_z": [[0.1, 1.00003], [1.0, 1.1], [4.0, 1.4]],
    "native_QED_n": [81, 161, 321],
    "native_QED_interval": [0.01, 20.0],
    "finite_difference_relative_steps": [1e-3, 5e-4],
    "finite_difference_rule": "five-point central, (-f(z+2h)+8f(z+h)-8f(z-h)+f(z-2h))/(12h)",
    "reference_Gauss_Legendre_n": [240, 480],
    "reference_u_interval": [0.0, 80.0],
    "production_stepper_or_trajectory": False,
    "source_constants_changed": False,
    "native_derivative_replaced": False,
}


def five_point(function, x, z, h):
    return (-function(x,z+2*h)+8*function(x,z+h)
            -8*function(x,z-h)+function(x,z-2*h))/(12*h)


def run(args):
    source = args.source.resolve()
    before = snapshot(source)
    sys.path.insert(0, str(source))
    import Constants as constants
    import Momentum_Grid as grid
    import Thermodynamics.Thermal_QED_corrections as qed
    grid.setupGrid(40.0, 301, 0.01)
    observations = []
    for n in DECLARATION["native_QED_n"]:
        # This is an explicit in-memory quadrature refinement, not a patch
        # to code or to the functions under test. Every function still
        # builds its own native Simpson rule using these native globals.
        grid.n_QED = n
        grid.dyQED = (grid.yQED_max-grid.yQED_min)/(n-1)
        for x,z in DECLARATION["states_x_z"]:
            direct = float(qed.dP_2dz(x,z))
            finite_differences = {
                str(relative): float(five_point(qed.P_2,x,z,z*relative))
                for relative in DECLARATION["finite_difference_relative_steps"]
            }
            actual_derivative = complex_partial(qed.P_2,x,z,"z")
            native_rho2,native_rho3 = qed.Thermal_QED_corrections_to_energy_density(x,z)
            p2 = float(qed.P_2(x,z))
            p3 = lambda xx,zz: constants.e**3*zz*qed.I(xx,zz)**1.5/(12*np.pi**4)
            rho3_pressure = z*complex_partial(p3,x,z,"z")-p3(x,z)
            refs = {
                str(nn): {key:float(value) for key,value in reference_plasma(x,z,constants.e,nn).items() if "qed" in key}
                for nn in DECLARATION["reference_Gauss_Legendre_n"]
            }
            observations.append({
                "x": x, "z": z, "native_QED_n": n,
                "native_P2": p2, "native_dP2dz": direct,
                "actual_derivative_complex_step": actual_derivative,
                "actual_derivative_finite_difference": finite_differences,
                "native_dP2dz_minus_actual": direct-actual_derivative,
                "native_derivative_relative_to_actual_minus_one": direct/actual_derivative-1,
                "native_rho2": float(native_rho2),
                "same_grid_pressure_identity_rho2": z*actual_derivative-p2,
                "native_rho2_minus_pressure_identity": float(native_rho2-(z*actual_derivative-p2)),
                "native_rho3": float(native_rho3),
                "same_grid_P3": float(p3(x,z)),
                "same_grid_pressure_identity_rho3": float(rho3_pressure),
                "native_rho3_over_pressure_identity": float(native_rho3/rho3_pressure),
                "expected_ratio_x2_over_z2": (x/z)**2,
                "reference_components": refs,
            })
    # Restore the native default quadrature within this short-lived worker.
    grid.n_QED = 81
    grid.dyQED = (grid.yQED_max-grid.yQED_min)/80
    after = snapshot(source)
    if after != before:
        raise RuntimeError("Official source changed during QED identity check")
    paper = args.output.parent / "2210.10307.pdf"
    receipt = {
        "scope": "Local native QED callable/pressure identity; no trajectory or observational effect",
        "declaration": DECLARATION,
        "runtime": {"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"executable":sys.executable},
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": str(source), "source_snapshot": before, "source_unchanged": True,
        "script_sha256": sha256(__file__), "independent_reference_script_sha256":sha256(Path(__file__).with_name("conservation_review.py")),
        "primary_reference": {"url":"https://arxiv.org/pdf/2210.10307", "pdf_sha256":sha256(paper) if paper.exists() else None,
                              "equations":["2.51","2.53","2.54"], "printed_page":20,
                              "retrieval": "Successful curl --fail --location with TLS verification; unversioned arxiv PDF downloaded 2026-10-02, metadata creation 2022-11-03"},
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(receipt,file,indent=2,sort_keys=True,allow_nan=False)
        file.write("\n")
    print(json.dumps({"output":str(args.output),"source_unchanged":True,
                      "default_n81":[row for row in observations if row["native_QED_n"]==81]},indent=2,allow_nan=False))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=Path("/workspace/shared/dmde-upstream/nudec"))
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args())
