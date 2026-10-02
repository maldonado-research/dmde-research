#!/usr/bin/env python3
"""Independent continuum checks using only public cards and upstream x(t).

The table-weighted result is a proxy, not a self-consistent injected solution.
No producer code or upstream Python modules are imported.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import platform
from pathlib import Path


def interp(v, points, values):
    i = bisect.bisect_right(points, v)
    if i == 0:
        return values[0]
    if i == len(points):
        return values[-1]
    w = (v - points[i-1]) / (points[i] - points[i-1])
    return values[i-1] * (1-w) + values[i] * w


def retained(flavor, order, u):
    """Exact clipped/full Michel physical-moment ratio, u=Emax/(m_mu/2)."""
    u = min(1., max(0., u))
    if flavor == 'e':
        return (order+4)*u**(order+3) - (order+3)*u**(order+4)
    return (3*(order+4)*u**(order+3) - 2*(order+3)*u**(order+4))/(order+6)


def simpson(f, a, b, n):
    step = (b-a)/n
    s = f(a)+f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2)*f(a+i*step)
    return s*step/3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nudec-dir', type=Path, required=True, help='Clean official public Nudec checkout')
    parser.add_argument('--cards-file', type=Path, required=True, help='Public frozen source-card JSON')
    parser.add_argument('--time-steps', type=int, default=100000)
    parser.add_argument('--output', type=Path, help='Create a new receipt; existing paths are rejected')
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f'Refusing to overwrite existing output: {args.output}')
    if args.time_steps < 4 or args.time_steps % 4:
        parser.error('--time-steps must be positive and divisible by four')
    upstream = args.nudec_dir.resolve()
    cards_file = args.cards_file.resolve()
    cards = json.loads(cards_file.read_text())
    tau = cards[0]['tau_s']
    me = 0.5109989
    mmu_native = 105.7
    mmu_frozen = cards[0]['m_mu_MeV']
    table = list(csv.reader((upstream / 'scaleFactorTime.csv').open()))
    xs, ts = zip(*((float(x), float(t)) for x, t in table))

    stop_t = 18*tau
    stop_x = interp(stop_t, ts, xs)
    clip_start_x = me*stop_x
    clip_start_t = interp(clip_start_x, xs, ts)
    norm = -math.expm1(-18.)


    def table_weighted_loss(flavor, order, steps):
        # For native qmax=x_stop*m_mu_native/2 and its own distribution endpoint,
        # u(t)=m_e*x_stop/x_table(t).  Frozen-mass qmax yields the same ratio.
        f = lambda t: math.exp(-t/tau)/tau * (1-retained(flavor, order, me*stop_x/interp(t, ts, xs)))
        return simpson(f, 0., stop_t, steps)/norm


    weighted = {}
    for flavor in ('e', 'mu'):
        for order in (0, 1, 5):
            fine = table_weighted_loss(flavor, order, args.time_steps)
            coarse = table_weighted_loss(flavor, order, args.time_steps//2)
            weighted[f'{flavor}_k{order}'] = {'loss': fine, 'abs_coarse_fine_difference': abs(fine-coarse)}

    mass_ratio = mmu_native/mmu_frozen
    cross_e = (1-mass_ratio**-3)/(1-mass_ratio**-4)
    e_cdf_max = retained('e',0,cross_e)-retained('e',0,cross_e/mass_ratio)
    mu_cdf_max = 1-retained('mu',0,1/mass_ratio)
    artifact = {
        'classification': 'independent_continuum_and_reference_table_proxy',
        'limits': [
            'The reported final-domain fractions are the x->x_stop- active-source limit; native injection is off at x_stop itself.',
            'Final-domain moment loss is instantaneous and is not integrated energy loss.',
            'Reference table weighting does not use an injected production background.',
            'Reference-table losses count upper-domain omissions in injected source moments only; lower-grid cutoffs and subsequent cosmological redshifting are absent.',
            'No collisions, oscillations, blocking, weak rates or BBN prediction are computed.',
            'No upstream Python module or producer validator is imported.',
        ],
        'constants': {'me_native_MeV': me, 'mmu_native_MeV': mmu_native, 'mmu_frozen_MeV': mmu_frozen},
        'runtime': {'python': platform.python_version()},
        'coordinate_convention': 'q is the numerical native code coordinate in p=q*me/x; no upstream MeV label is adopted for q; x=a*me and physical p is in MeV.',
        'time_quadrature_steps': args.time_steps,
        'reference_stop': {'t_s': stop_t, 'x': stop_x},
        'endpoint': {
            'qmax_native_formula_code_coordinate': stop_x*mmu_native/2,
            'qmax_frozen_formula_code_coordinate': stop_x*mmu_frozen/2,
            'qmax_frozen_complete_code_coordinate': stop_x*mmu_frozen/(2*me),
            'native_Emax_final_MeV': me*mmu_native/2,
            'frozen_formula_Emax_final_MeV': me*mmu_frozen/2,
            'native_profile_endpoint_MeV': mmu_native/2,
            'frozen_profile_endpoint_MeV': mmu_frozen/2,
            'native_cut_fraction_u': me,
            'clip_start_x_reference': clip_start_x,
            'clip_start_t_s_reference': clip_start_t,
            'clip_start_t_over_tau_reference': clip_start_t/tau,
        },
        'active_limit_x_to_stop_moment_retained_fraction': {
            flavor: [retained(flavor,k,me) for k in range(6)] for flavor in ('e','mu')
        },
        'native_frozen_mass_mismatch': {
            'relative_mass': mass_ratio-1,
            'native_moment_relative_error_full_endpoint': [mass_ratio**k-1 for k in range(6)],
            'number_mass_above_frozen_endpoint': {
                flavor: 1-retained(flavor,0,1/mass_ratio) for flavor in ('e','mu')
            },
            'full_continuum_normalized_shape_L1': {'e':2*e_cdf_max, 'mu':2*mu_cdf_max},
            'full_continuum_CDF_max': {'e':e_cdf_max, 'mu':mu_cdf_max},
            'e_density_crossing_energy_MeV': cross_e*mmu_frozen/2,
        },
        'reference_table_weighted_moment_loss': weighted,
        'reference_table_weighted_total_number_loss': (weighted['e_k0']['loss'] + weighted['mu_k0']['loss'])/2,
        'reference_table_weighted_total_energy_loss': (0.6*weighted['e_k1']['loss'] + 0.7*weighted['mu_k1']['loss'])/1.3,
        'reference_start': {
            'T_MeV': 1.00003*me/.1,
            's_MeV3': 2*math.pi**2/45*10.75*(1.00003*me/.1)**3,
            'card_nstart_MeV3': {card['blind_id']:card['Y0']*2*math.pi**2/45*10.75*(1.00003*me/.1)**3 for card in cards},
        },
        'public_inputs_sha256': {'provider/public_source_cards': hashlib.sha256(cards_file.read_bytes()).hexdigest(), **{f'nudec/{name}':hashlib.sha256((upstream/name).read_bytes()).hexdigest() for name in ('scaleFactorTime.csv','Constants.py','Core.py','System_Nudecoupling.py','Distributions.py')}},
    }
    rendered = json.dumps(artifact, indent=2, allow_nan=False)+'\n'
    if args.output is not None:
        with args.output.open('x') as stream:
            stream.write(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
