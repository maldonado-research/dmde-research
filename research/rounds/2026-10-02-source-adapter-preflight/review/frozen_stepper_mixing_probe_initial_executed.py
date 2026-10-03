#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Public upstream mixing witness; no solver, collision evaluation or payload.

This authored review script imports GPL-3.0-only Nudec modules without copying
their implementation. Upstream: baugid/Nudec_LLP_Solver, commit
0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62. No upstream file is modified.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import beta as beta_distribution

UPSTREAM = Path('/workspace/shared/dmde-upstream/nudec')
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(UPSTREAM))
import Constants
import Distributions
import Momentum_Grid
import System_Nudecoupling


def source_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in UPSTREAM.glob('*.py')}


before = source_hashes()
original_mass = Distributions.mmu
Distributions.mmu = 105.6583755
x = 4.0
z = 1.4
Momentum_Grid.setupGrid(x * Distributions.mmu / (2 * Constants.me), 513)
p = Momentum_Grid.gridVals * Constants.me / x
source = Distributions.muonDistribution(p, x, {'mu': 1.0, 'pi': 1.0})
probability = System_Nudecoupling.calcMixingMatrixes(z * Constants.me / x, p)
transport_injection = np.einsum('ijk,ki->ji', probability, source)
pre_peak = float(np.max(source))
tau_scaled = float(np.max(transport_injection[2]) / pre_peak)
sum_error = float(np.max(np.abs(np.sum(transport_injection, axis=0)
                                - np.sum(source, axis=0))) / pre_peak)

# The following fixed points are declared in these source bytes before this
# run; their source values use a beta-density representation independent of
# the upstream Michel implementation. The mixing reconstruction uses explicit
# PMNS entries rather than the upstream rotation-matrix helper.
temperatures = [0.05, 0.1, 0.5, 1.0, 5.0]
physical_points = np.array([0.01, 0.1, 1.0, 10.0, 25.0, 40.0,
                            Distributions.mmu / 2])
Momentum_Grid.n = len(physical_points)
actual_source_points = Distributions.muonDistribution(
    physical_points, x, {'mu': 1.0, 'pi': 1.0})
u = physical_points / (Distributions.mmu / 2)
independent_source_points = np.array([
    beta_distribution.pdf(u, 3, 2),
    2 * beta_distribution.pdf(u, 3, 1) - beta_distribution.pdf(u, 4, 1),
    np.zeros_like(u),
]) / (Distributions.mmu / 2)
source_point_error = float(np.max(np.abs(actual_source_points
                                          - independent_source_points))
                           / np.max(independent_source_points))
rows = []
mixing_independent_error = 0.0
for temperature in temperatures:
    native_probability = System_Nudecoupling.calcMixingMatrixes(
        temperature, physical_points)
    for index, momentum in enumerate(physical_points):
        matter_term = Constants.MSWPrefactor * momentum**2 * temperature**4
        theta12 = .5 * math.atan2(Constants.ds12,
                                 Constants.dc12 + matter_term / Constants.Dm21sq)
        theta13 = .5 * math.atan2(Constants.ds13,
                                 Constants.dc13 + matter_term / Constants.Dm31sq)
        a, b = math.sin(theta12), math.cos(theta12)
        d, e = math.sin(theta13), math.cos(theta13)
        g, h = Constants.s23, Constants.c23
        pmns = np.array([
            [b*e, a*e, d],
            [-a*h-b*g*d, b*h-a*g*d, g*e],
            [a*g-b*h*d, -b*g-a*h*d, h*e],
        ])
        independent_probability = (pmns**2) @ (pmns**2).T
        mixing_independent_error = max(
            mixing_independent_error,
            float(np.max(np.abs(independent_probability-native_probability[index]))))
        mixed_point = native_probability[index] @ actual_source_points[:, index]
        premixed_point = actual_source_points[:, index]
        rows.append({
            'T_gamma_MeV': temperature,
            'p_MeV': float(momentum),
            'premixing_source_e_per_MeV': float(premixed_point[0]),
            'premixing_source_mu_per_MeV': float(premixed_point[1]),
            'premixing_source_tau_per_MeV': float(premixed_point[2]),
            'mixed_source_e_per_MeV': float(mixed_point[0]),
            'mixed_source_mu_per_MeV': float(mixed_point[1]),
            'mixed_source_tau_per_MeV': float(mixed_point[2]),
            'tau_fraction_of_total_source': float(mixed_point[2] / np.sum(premixed_point)),
        })

# A one-helicity canonical conversion and scalar source amplitude multiply all
# three arrays equally and cannot remove this nonzero tau response. In a full
# mixed production stepper, the on/off derivative differs from the pre-mixing
# source at order h^0 after dividing its finite response by h.
receipt = {
    'classification': 'public_source_mixing_diagnostic',
    'source_commit': '0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62',
    'grid_nodes': 513,
    'x': x,
    'z': z,
    'T_gamma_MeV': z * Constants.me / x,
    'native_muon_mass_before_MeV': original_mass,
    'emitter_muon_mass_override_MeV': Distributions.mmu,
    'override_scope': 'Distributions.mmu only; diagnostic source consumer',
    'pre_mixing_tau_max_abs': float(np.max(np.abs(source[2]))),
    'mixed_tau_peak_over_premixing_source_peak': tau_scaled,
    'mixed_total_source_flavor_sum_peak_scaled_error': sum_error,
    'frozen_tau_response_ceiling': 1e-14,
    'native_unsplit_mixed_stepper_incompatible_with_frozen_tau_response_gate': tau_scaled > 1e-14,
    'rationale': ('Native full mixed evolution has nonzero tau source response '
                  'even in the infinitesimal-step limit; a declared pre-mixing '
                  'source substep is different evidence; no universal '
                  'incompatibility with physical operator splitting is claimed.'),
    'fixed_point_temperatures_MeV': temperatures,
    'fixed_point_momenta_MeV': physical_points.tolist(),
    'independent_beta_source_point_peak_scaled_error': source_point_error,
    'independent_explicit_PMNS_probability_max_abs_error': mixing_independent_error,
    'fixed_point_tau_fraction_of_total_source_min': min(row['tau_fraction_of_total_source'] for row in rows),
    'fixed_point_tau_fraction_of_total_source_max': max(row['tau_fraction_of_total_source'] for row in rows),
    'fixed_point_samples': rows,
    'source_hashes_before': before,
    'source_hashes_after': source_hashes(),
    'source_files_unchanged': before == source_hashes(),
    'probe_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(OUT / 'frozen_stepper_mixing_probe.json').write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + '\n')
np.savetxt(OUT / 'frozen_stepper_mixing_samples.csv',
           np.column_stack((p, source.T, transport_injection.T)), delimiter=',',
           header='p_MeV,pre_e,pre_mu,pre_tau,mixed_e,mixed_mu,mixed_tau', comments='')
assert receipt['source_files_unchanged']
assert receipt['pre_mixing_tau_max_abs'] == 0
assert sum_error < 1e-12
assert receipt['native_unsplit_mixed_stepper_incompatible_with_frozen_tau_response_gate']
assert source_point_error < 1e-12
assert mixing_independent_error < 1e-12
print(json.dumps({k: receipt[k] for k in (
    'mixed_tau_peak_over_premixing_source_peak',
    'mixed_total_source_flavor_sum_peak_scaled_error',
    'native_unsplit_mixed_stepper_incompatible_with_frozen_tau_response_gate',
    'independent_beta_source_point_peak_scaled_error',
    'independent_explicit_PMNS_probability_max_abs_error',
    'fixed_point_tau_fraction_of_total_source_min',
    'fixed_point_tau_fraction_of_total_source_max',
    'source_files_unchanged')}, sort_keys=True))
