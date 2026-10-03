#!/usr/bin/env python3
"""Alternate quadrature/interpolation checks of reference-table source loss.

No upstream code is imported. PCHIP comparison is interpolation sensitivity,
not an error estimate for an unknown physical production history.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad, simpson
from scipy.interpolate import PchipInterpolator


def retained(flavor, order, u):
    u = np.clip(u,0.,1.)
    if flavor=='e':
        return (order+4)*u**(order+3)-(order+3)*u**(order+4)
    return (3*(order+4)*u**(order+3)-2*(order+3)*u**(order+4))/(order+6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nudec-dir', type=Path, required=True, help='Clean official public Nudec checkout')
    parser.add_argument('--cards-file', type=Path, required=True, help='Public frozen source-card JSON')
    parser.add_argument('--output', type=Path, help='Create a new receipt; existing paths are rejected')
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f'Refusing to overwrite existing output: {args.output}')
    cards_file = args.cards_file.resolve()
    table_file = args.nudec_dir.resolve()/'scaleFactorTime.csv'
    tau = json.loads(cards_file.read_text())[0]['tau_s']
    xs, ts = np.array([(float(x),float(t)) for x,t in csv.reader(table_file.open())]).T
    stop_t = 18*tau
    stop_x = float(np.interp(stop_t, ts, xs))
    me = .5109989
    norm = -math.expm1(-18.)
    pchip = PchipInterpolator(ts, xs, extrapolate=False)

    def loss_integrand(t, flavor, order, x_at_t):
        return np.exp(-np.asarray(t)/tau)/tau*(1-retained(flavor,order,me*stop_x/x_at_t(t)))/norm


    def adaptive_panel_integral(flavor, order, x_at_t):
        clip_start_t=float(np.interp(me*stop_x,xs,ts))
        edges=sorted(set([0.,clip_start_t,stop_t]+[float(t) for t in ts if 0<t<stop_t]))
        nodes,weights=np.polynomial.legendre.leggauss(16)
        gl_sum=0.
        quad_sum=0.
        quad_error=0.
        for a,b in zip(edges[:-1],edges[1:]):
            half=(b-a)/2
            t=(a+b)/2+half*nodes
            gl_sum += half*float(np.dot(weights,loss_integrand(t,flavor,order,x_at_t)))
            value,error=quad(lambda t:float(loss_integrand(t,flavor,order,x_at_t)),a,b,epsabs=1e-15,epsrel=1e-12)
            quad_sum+=value
            quad_error+=error
        return {'panel_GL16':gl_sum,'panel_adaptive_quad':quad_sum,'quad_internal_abs_error_sum':quad_error,'abs_GL_quad_difference':abs(gl_sum-quad_sum)}


    linear=lambda t:np.interp(t,ts,xs)
    result={
        'classification':'reference_table_proxy_quadrature_and_interpolation_sensitivity_only',
        'scope':'fixed native upper code coordinate, continuum Michel source, public table x(t); upper-domain omitted injected source moments only, no lower-grid cutoff or subsequent redshifting, no transport, evolved spectra, rate or abundance result',
        'x_stop_policy':'fixed to native Core piecewise-linear table x(18tau) for every comparison',
        'reference_stop_t_s':stop_t,'reference_stop_x':stop_x,
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'cases':{},
        'inputs_sha256':{'nudec/scaleFactorTime.csv':hashlib.sha256(table_file.read_bytes()).hexdigest(),'provider/public_source_cards':hashlib.sha256(cards_file.read_bytes()).hexdigest()},
    }
    for flavor in ('e','mu'):
        for order in (0,1,5):
            lin=adaptive_panel_integral(flavor,order,linear)
            cubic=adaptive_panel_integral(flavor,order,pchip)
            dense=[]
            for n in (5001,10001,20001):
                t=np.linspace(0.,stop_t,n)
                dense.append({'n_times':n,'uniform_Simpson_loss':float(simpson(loss_integrand(t,flavor,order,linear),x=t))})
            result['cases'][f'{flavor}_k{order}']={
                'piecewise_linear':lin,'PCHIP':cubic,'uniform_time_resolution':dense,
                'abs_PCHIP_linear_difference':abs(lin['panel_adaptive_quad']-cubic['panel_adaptive_quad']),
                'PCHIP_comparison_interpretation':'Interpolation sensitivity, not a production-history uncertainty bound.',
            }
    for method in ('piecewise_linear','PCHIP'):
        result[f'{method}_total_energy_loss']=(.6*result['cases']['e_k1'][method]['panel_adaptive_quad']+.7*result['cases']['mu_k1'][method]['panel_adaptive_quad'])/1.3
    result['total_energy_loss_abs_interpolation_difference']=abs(result['piecewise_linear_total_energy_loss']-result['PCHIP_total_energy_loss'])
    rendered = json.dumps(result, indent=2, allow_nan=False)+'\n'
    if args.output is not None:
        with args.output.open('x') as stream:
            stream.write(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
