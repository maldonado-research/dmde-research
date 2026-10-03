#!/usr/bin/env python3
"""Independent local energy audit of the saved public native RHS fixture.

This imports native thermodynamics and grid functions, never System_Nudec,
collisions, provider validators, private data or a production solution.  It
does not repair upstream thermodynamics or normalize a truncated spectrum.
The standard pressure reference is independently transcribed from ideal
g=4 electrons plus the e^2/e^3 pressure equations of state.  Two fixed
Gauss-Legendre rules verify its numerical stability; they are diagnostics,
not an exploratory fit or a cosmological uncertainty estimate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.special import expit

EXPECTED_HEAD = "0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62"


def read_json(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(source):
    def git(*args):
        return subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(source), *args], text=True
        ).strip()
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    if head != EXPECTED_HEAD or status:
        raise RuntimeError("Expected clean pinned official source")
    paths = sorted(filter(None, git("ls-files", "-z").split("\0")))
    return {"head": head, "porcelain": status,
            "tracked_sha256": {p: sha256(source / p) for p in paths}}


def reference_plasma(x, z, coupling, n):
    # The integration coordinate u=p/T is dimensionless. u_max=80 bounds
    # the omitted thermal tail by a polynomial times exp(-80).
    nodes, weights = leggauss(n)
    u = 40.0 * (nodes + 1.0)
    weights = 40.0 * weights
    epsilon = np.sqrt(u*u + (x/z)**2)
    f = 1.0 / (np.exp(epsilon) + 1.0)
    ff = f * (1.0 - f)
    integrate = lambda values: np.dot(weights, values)
    re = 2*z**4/math.pi**2 * integrate(u*u*epsilon*f)
    pe = 2*z**4/(3*math.pi**2) * integrate(u**4/epsilon*f)
    tmp = 2*z*z * integrate(u*u/epsilon*f)
    tmp_z = 2*z * integrate(u*u*ff)
    integral = 2*z*z * integrate((2*u*u+(x/z)**2)/epsilon*f)
    integral_z = 2*z * integrate((2*u*u+(x/z)**2)*ff)
    p2 = -coupling**2*z*z*tmp/(12*math.pi**2) - coupling**2*tmp*tmp/(8*math.pi**4)
    p2z = (-coupling**2*z*tmp/(6*math.pi**2)
           -coupling**2*z*z*tmp_z/(12*math.pi**2)
           -coupling**2*tmp*tmp_z/(4*math.pi**4))
    r2 = -p2 + z*p2z
    p3 = coupling**3*z*integral**1.5/(12*math.pi**4)
    r3 = coupling**3*z*z*np.sqrt(integral)*integral_z/(8*math.pi**4)
    rg = math.pi**2*z**4/15.0
    return {"rho_gamma": rg, "pressure_gamma": rg/3,
            "rho_e": re, "pressure_e": pe,
            "rho_qed2": r2, "pressure_qed2": p2,
            "rho_qed3": r3, "pressure_qed3": p3}


def totals(components):
    return (sum(value for key, value in components.items() if key.startswith("rho_")),
            sum(value for key, value in components.items() if key.startswith("pressure_")))


def complex_partial(function, x, z, coordinate):
    h = 1e-25
    args = (x+1j*h, z) if coordinate == "x" else (x, z+1j*h)
    return float(np.imag(function(*args))/h)


def run(args):
    source = args.source.resolve()
    fixture = args.fixture.resolve()
    before = snapshot(source)
    metadata = read_json(fixture / "result.json")
    declaration = metadata["configuration"]
    x = declaration["rhs_x"]
    count = declaration["rhs_llp_count"]
    mass = declaration["rhs_mass_MeV"]
    tau = declaration["rhs_lifetime_seconds"]
    sys.path.insert(0, str(source))
    import Constants as constants
    import Momentum_Grid as grid
    import Thermodynamics.Thermodynamics_ideal_gas as ideal
    import Thermodynamics.Thermal_QED_corrections as qed
    grid.setupGrid(metadata["q_max"], declaration["rhs_n"], declaration["q_min"])
    q, weights = grid.gridVals, grid.gridWeights
    state = np.loadtxt(fixture / "fixed_state.csv", delimiter=",", skiprows=1)[:, 1]
    f = state[:3*grid.n].reshape(3, grid.n)
    z, t = state[-2:]
    rho_nu = float(np.sum(weights*q**3*np.sum(f, axis=0))/math.pi**2)
    # Six one-helicity species; the three native distributions are copied
    # to antiparticles. The ideal e± g=4 factor is already correct upstream.
    def native_plasma(xx, zz):
        electron_energy = np.sqrt(q*q+xx*xx)
        fd = 1/(np.exp(electron_energy/zz)+1)
        re = 2/math.pi**2*np.sum(weights*q*q*electron_energy*fd)
        pe = 2/(3*math.pi**2)*np.sum(weights*q**4/electron_energy*fd)
        r2, r3 = qed.Thermal_QED_corrections_to_energy_density(xx, zz)
        p2 = qed.P_2(xx, zz)
        # The backend ships no P3 callable. The only pressure used here is
        # the declared Debye/ring pressure on the same native QED grid.
        p3 = constants.e**3*zz*qed.I(xx, zz)**1.5/(12*math.pi**4)
        rg = math.pi**2*zz**4/15
        return {"rho_gamma": rg, "pressure_gamma": rg/3,
                "rho_e": re, "pressure_e": pe,
                "rho_qed2": r2, "pressure_qed2": p2,
                "rho_qed3": r3, "pressure_qed3": p3}
    def independent_local(plasma, rhs, parent_count, gate):
        rpl, ppl = totals(plasma(x, z))
        rpx = complex_partial(lambda xx, zz: totals(plasma(xx, zz))[0], x, z, "x")
        rpz = complex_partial(lambda xx, zz: totals(plasma(xx, zz))[0], x, z, "z")
        rparent = mass*parent_count*math.exp(-t/tau)*x/constants.me
        rnu_prime = float(np.sum(weights*q**3*np.sum(rhs[:3*grid.n].reshape(3, grid.n), axis=0))/math.pi**2)
        derivative = rpx+rpz*rhs[-2]+rnu_prime+rparent*(1/x-rhs[-1]/tau)
        trace_over_x = (rpl-3*ppl+rparent)/x
        residual = derivative-trace_over_x
        j, yy = ideal.Functions_in_z_ideal_gas(x, z)
        g21, g22, g31, g32 = qed.Thermal_QED_corrections_to_z(x, z)
        native_capacity = 2*z**3*((x/z)**2*j+yy+2*math.pi**2/15+g22+g32)
        native_heating = 2*z**3*((x/z)*j+g21+g31)
        parent_decay = rparent*rhs[-1]/tau
        algebra = native_capacity*rhs[-2]+rnu_prime-native_heating-int(gate)*parent_decay
        decomposition = ((rpz-native_capacity)*rhs[-2]
                         +rpx-(rpl-3*ppl)/x+native_heating
                         -(1-int(gate))*parent_decay)
        return {"plasma_components_barred": {k: float(v) for k,v in plasma(x,z).items()},
                "rho_nu_bar": rho_nu, "rho_parent_bar": rparent,
                "rho_total_bar": rpl+rho_nu+rparent,
                "plasma_partial_x": rpx, "plasma_partial_z": rpz,
                "rho_nu_prime": rnu_prime, "rho_parent_decay_per_dx": parent_decay,
                "rho_total_prime": float(derivative), "trace_over_x": float(trace_over_x),
                "continuity_residual_per_dx": float(residual),
                "continuity_over_H_rho": float(x*residual/(rpl+rho_nu+rparent)),
                "native_rhs_algebraic_cancellation": float(algebra),
                "independent_decomposition_residual_per_dx": float(decomposition),
                "decomposition_minus_direct": float(decomposition-residual),
                "native_temperature_capacity": float(native_capacity),
                "native_temperature_heating": float(native_heating)}
    rows = {}
    for lane in ("zero_off", "positive_off", "positive_on"):
        rhs = np.loadtxt(fixture / f"rhs_{lane}.csv", delimiter=",", skiprows=1)[:,1]
        parent_count = 0 if lane == "zero_off" else count
        rows[lane] = {"native_energy_inferred_pressure": independent_local(native_plasma, rhs, parent_count, lane.endswith("on")),
                      "reference_energy_pressure_n240": independent_local(lambda xx,zz: reference_plasma(xx,zz,constants.e,240), rhs, parent_count, lane.endswith("on")),
                      "reference_energy_pressure_n480": independent_local(lambda xx,zz: reference_plasma(xx,zz,constants.e,480), rhs, parent_count, lane.endswith("on"))}
    tmp = (qed.P_2(x,z), qed.dP_2dz(x,z))
    identity = {"native_P2": float(tmp[0]), "native_dP2dz": float(tmp[1]),
                "derivative_of_native_P2": complex_partial(qed.P_2,x,z,"z"),
                "native_rho3": float(qed.Thermal_QED_corrections_to_energy_density(x,z)[1]),
                "same_grid_pressure_identity_rho3": float(constants.e**3*z*z*np.sqrt(qed.I(x,z))*qed.dIdz(x,z)/(8*math.pi**4)),
                "rho3_native_over_pressure_identity": float((x/z)**2)}
    after = snapshot(source)
    if before != after:
        raise RuntimeError("Official source changed during calculation")
    outcome = {"scope": "Local audit of public saved n=21 RHS; no new RHS, transport or BBN solve",
               "x": x, "z": float(z), "t_s": float(t), "parent_count": count,
               "tau_s": tau, "mass_MeV": mass, "source": str(source), "source_snapshot": before,
               "source_unchanged": True, "script_sha256": sha256(__file__),
               "fixture_sha256": {p.name: sha256(p) for p in sorted(fixture.glob("*.csv"))},
               "fixture_result_sha256": sha256(fixture/"result.json"),
               "pressure_convention": "Ideal photon/e±/nu; e^2 native P2; e^3 Debye ring P3=e^3*z*I^(3/2)/(12*pi^4); pressureless parent",
               "reference_convention": "Ideal e± and QED reference integrals independent Gauss-Legendre u=p/T in [0,80]; six neutrino moment retained on actual native grid",
               "native_QED_identity": identity, "rows": rows,
               "tail_cutoff": {"exp_minus_18": math.exp(-18), "omitted_rest_energy_over_initial_parent_rest_energy": math.exp(-18),
                               "warning": "This is a parent rest-energy fraction, not a total-energy or final-observable bound"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(outcome, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")
    print(json.dumps({"output": str(args.output), "native_QED_identity": identity,
                      "residuals_over_H_rho": {key:{k:v["continuity_over_H_rho"] for k,v in value.items()} for key,value in rows.items()},
                      "source_unchanged": True}, indent=2, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("/workspace/shared/dmde-upstream/nudec"))
    parser.add_argument("--fixture", type=Path, default=Path("/workspace/dmde-research/research/rounds/2026-10-01-transport-source-audit/native-probe/results-2026-10-01-final-rhs/rhs_n21"))
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
