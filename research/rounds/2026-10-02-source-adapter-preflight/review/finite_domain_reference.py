#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Independent beta-distribution Michel references for adapter review.

This does not import the producer adapter, provider validator or upstream
emitter. The representation follows dimensionless normalized beta densities:
electron = Beta(3,2), muon = 2 Beta(3,1) - Beta(4,1).
"""
import math

import numpy as np
from scipy.special import beta, betainc
from scipy.stats import beta as beta_distribution

FROZEN_MUON_MASS_MEV = 105.6583755
REFERENCE_ELECTRON_MASS_MEV = 0.5109989
REFERENCE_X0 = 0.1
REFERENCE_Z0 = 1.00003
REFERENCE_GSTARS = 10.75


def reference_entropy_start():
    temperature = (REFERENCE_Z0 * REFERENCE_ELECTRON_MASS_MEV
                   / REFERENCE_X0)
    return 2 * math.pi**2 / 45 * REFERENCE_GSTARS * temperature**3


def fixed_state_coefficient(q):
    """One-helicity one-charge f -> dY/dq factor, independent of x."""
    comoving_entropy = reference_entropy_start() * (
        REFERENCE_X0 / REFERENCE_ELECTRON_MASS_MEV)**3
    return np.asarray(q)**2 / (2 * math.pi**2 * comoving_entropy)


def truncated_beta_moment(shape_a, shape_b, order, lo, hi):
    weighted_norm = beta(shape_a + order, shape_b) / beta(shape_a, shape_b)
    return weighted_norm * (betainc(shape_a + order, shape_b, hi)
                            - betainc(shape_a + order, shape_b, lo))


def physical_moment(flavor, order, lower_p, upper_p):
    """Exact finite-domain moment via regularized incomplete beta functions."""
    endpoint = FROZEN_MUON_MASS_MEV / 2
    lo = max(0.0, min(1.0, float(lower_p) / endpoint))
    hi = max(0.0, min(1.0, float(upper_p) / endpoint))
    if hi <= lo:
        return 0.0
    if flavor == 'e':
        unit_moment = truncated_beta_moment(3, 2, order, lo, hi)
    elif flavor == 'mu':
        unit_moment = (2 * truncated_beta_moment(3, 1, order, lo, hi)
                       - truncated_beta_moment(4, 1, order, lo, hi))
    else:
        raise ValueError('flavor must be e or mu')
    return endpoint**order * float(unit_moment)


def canonical_source(q, x, t_s, tau_s, yield0, branch):
    """Independent canonical pre-mixing source, charges aliased explicitly."""
    q = np.asarray(q)
    c = REFERENCE_ELECTRON_MASS_MEV / x
    u = q * c / (FROZEN_MUON_MASS_MEV / 2)
    if 0 <= t_s < 18 * tau_s:
        scale = branch * yield0 * math.exp(-t_s / tau_s) / tau_s
    else:
        scale = 0.0
    per_q = c / (FROZEN_MUON_MASS_MEV / 2)
    e = scale * per_q * beta_distribution.pdf(u, 3, 2)
    mu = scale * per_q * (2 * beta_distribution.pdf(u, 3, 1)
                         - beta_distribution.pdf(u, 4, 1))
    zero = np.zeros_like(q)
    return np.array([e, e.copy(), mu, mu.copy(), zero, zero.copy()])
