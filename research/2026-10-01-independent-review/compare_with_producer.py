#!/usr/bin/env python3
"""Compare independent electron-energy integration with the producer's rate table.

Print a fresh JSON receipt; optionally save to a new path. Historical receipts
and the producer's outputs are never overwritten.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import numpy as np
import scipy

import independent_rates as independent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--producer-dir',type=Path,required=True,
                        help='Directory containing equilibrium_audit.py')
    parser.add_argument('--output',type=Path,
                        help='Optional new JSON file, never overwritten; default stdout only.')
    args=parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f'Refusing to overwrite existing output: {args.output}')
    producer_file=args.producer_dir.resolve()/'equilibrium_audit.py'
    spec=importlib.util.spec_from_file_location('reviewed_equilibrium_audit',producer_file)
    producer=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    if (producer.M_E,producer.DELTA,producer.TAU_N)!=(independent.ME,independent.Q,independent.TAU):
        raise ValueError('Producer/independent constants differ; specify a matched comparison.')
    comparisons=[]
    for temperature in producer.TEMPERATURES:
        ref=independent.rates(temperature)
        reference=np.array([ref[k] for k in ['n_nu','n_ep','beta','p_an','p_e','inverse']])
        actual=producer.thermal_rates(temperature)
        if not np.all(np.isfinite(actual)) or not np.all(reference>0):
            raise ValueError('Comparison requires finite, positive coefficients.')
        comparisons.append({'T_MeV':temperature,
                            'max_abs_relative_difference':float(np.max(np.abs(actual/reference-1)))})
    maximum=max(row['max_abs_relative_difference'] for row in comparisons)
    result={
        'method':'Independent electron-energy scipy.quad vs producer NumPy Gauss-Legendre',
        'status':'PASS_REFERENCE_CONSISTENCY_ONLY' if maximum<1e-10 else 'FAIL',
        'scope':'Static Born reference integration only; no production BBN or DMDE inference.',
        'python_version':platform.python_version(),
        'numpy_version':np.__version__,
        'scipy_version':scipy.__version__,
        'source_sha256':{
            'independent_rates.py':sha(Path(independent.__file__)),
            'compare_with_producer.py':sha(Path(__file__)),
            'equilibrium_audit.py':sha(producer_file),
        },
        'comparisons':comparisons,
        'max_abs_relative_difference':maximum,
        'i0_relative_difference':producer.analytic_i0()/independent.I0-1,
    }
    receipt=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.output is not None:
        with args.output.open('x') as stream:
            stream.write(receipt)
    print(receipt,end='')
    return 0 if maximum<1e-10 else 1


if __name__=='__main__':
    raise SystemExit(main())
