# Actual source-operator closure gate

## Gap closed

v0.9.17 validated scalar decay and energy histories and then reconstructed ideal Michel spectra internally to test whether the returned momentum grid could represent them. That established grid adequacy, but it did not inspect the momentum-resolved injection operator actually used by the backend.

Consequently, a backend could omit, double, flavor-swap, or misnormalize its production source RHS while returning correct scalar bookkeeping, a grid that represents an independently reconstructed ideal spectrum, and otherwise plausible histories. Raw code review could reveal the problem later, but the machine firewall did not reject it directly.

v0.9.20 therefore requires the actual production injection RHS in a canonical representation.

## Canonical arrays

Let

\[
D(t)=Y_0\frac{e^{-t/\tau}}{\tau},\qquad
p(t,q)=q\,c(t),\qquad c(t)=p_{\rm per\,q}(t).
\]

The bridge exports six arrays with shape `(Nt,Nq)` and units `dY_per_dt_dq_s^-1`:

```text
source_rhs_nue_dYdt_dq_s_inv
source_rhs_nuebar_dYdt_dq_s_inv
source_rhs_numu_dYdt_dq_s_inv
source_rhs_numubar_dYdt_dq_s_inv
source_rhs_nutau_dYdt_dq_s_inv
source_rhs_nutaubar_dYdt_dq_s_inv
```

They must be taken before collision and oscillation terms are added. If the native source is expressed per physical momentum, the canonical conversion contains the Jacobian `dp/dq=c(t)`.

With

\[
F_e(x)=12x^2(1-x),\qquad
F_\mu(x)=2x^2(3-2x),\qquad
x=\frac{2p}{m_\mu},
\]

the canonical densities are

\[
K_{a,q}(t,q)=c(t)\frac{2}{m_\mu}
F_a\!\left(\frac{2q\,c(t)}{m_\mu}\right).
\]

The frozen pair contract requires

\[
S_{\nu_e}=S_{\bar\nu_e}=B_{\mu\mu}D(t)K_{e,q},
\]

\[
S_{\nu_\mu}=S_{\bar\nu_\mu}=B_{\mu\mu}D(t)K_{\mu,q},
\qquad S_{\nu_\tau}=S_{\bar\nu_\tau}=0.
\]

All six arrays are zero after the frozen `18 tau` cutoff.

## Gates

For electron and muon flavor and every `k=0,...,5`, the validator computes

\[
\sum_i w_i\,p_i^k S_{a,i}(t)
\]

at every active history row and compares it with

\[
B_{\mu\mu}D(t)
\left(\frac{m_\mu}{2}\right)^kM_{a,k},
\]

where

\[
M_{e,k}=\frac{12}{(k+3)(k+4)},\qquad
M_{\mu,k}=\frac{2(k+6)}{(k+3)(k+4)}.
\]

The moment maximum relative error remains `5e-3`, but moments are no longer
the identifying gate. At every active row the returned source is compared with
the discrete canonical source on the identical nodes. The expected-mass
weighted-L1 and normalized-CDF ceilings are `5e-4`, the peak-scaled pointwise
ceiling is `5e-3`, and support above `m_mu/2` is zero. The exact source interval
is half-open, `0 <= t < 18 tau`; a row at the cutoff is explicitly source-off.
The scalar and actual two-dimensional time integrals close at `5e-5`.

The validator also requires:

\[
\dot N_\nu^{\rm total}=4B_{\mu\mu}D(t)
=2N_\mu^{\rm native}D(t),
\]

\[
\dot Q_\nu/s=f_\nu m_R D(t)
=1.3B_{\mu\mu}m_\mu D(t),
\]

electron- and muon-flavor neutrino/antineutrino equality, zero tau source, nonnegative finite arrays, and zero post-cutoff support.

## Provenance boundary

The metadata and raw solver configuration must agree on:

- `source_rhs_stage=pre_collision_pre_oscillation`;
- `source_rhs_units=dY_per_dt_dq_s^-1`;
- the production callable and module/symbol;
- the native-to-canonical normalization adapter;
- the export method; and
- a source-only impulse-test command invoking the same callable.

The bridge additionally binds the six occupation histories to canonical
`dY/dq` states. At eight fixed `t/tau` targets it derives the source response
from paired production-stepper outputs with the source on and off at `h` and
`h/2`; weighted-L1 and moments through fifth order must agree with the already
validated RHS within `5e-3` and converge under halving.

Machine validation cannot prove that a provider fabricated no mutually
consistent sidecar. The hashed code artifact, callable provenance, paired
operator replay, logs, and independent review remain necessary.

This gate changes no frozen source value and produces no BBN prediction.
