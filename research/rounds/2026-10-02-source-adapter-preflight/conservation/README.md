# Independent adapter conservation review — 2 October 2026

This AI-assisted review uses only the clean official NuDec checkout pinned at
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`, frozen public provider documents,
and the prior public `2026-10-01-transport-source-audit` fixture. It edits no
official source, provider file or root repository. It uses no private archive,
blinded NPZ payload, exploratory parameter tuning, production transport
trajectory, weak-rate history or BBN calculation. The calculations and notes
below are a numerical/software diagnostic, not external peer review.

## Result that limits the next adapter

Two native QED energy expressions disagree with pressure thermodynamics.
Native `dP_2dz` has a denominator `4*pi^2` where differentiation of native
`P_2` requires `4*pi^4`; native `rho_3` uses `x^2` where the stated equation
of state requires `z^2`. Literal native Hubble energy and native temperature
evolution therefore do not share a consistent QED energy/pressure reference.
A source callback can be instrumented without silently repairing these
functions, but a self-consistent total-energy trajectory claim needs a
separately reviewed, explicitly versioned correction or a declared diagnostic
limitation. These are local equation/callable findings; no observational
effect is estimated.

Native ideal-electron energy has the correct `2/pi^2` coefficient for four
electron/positron degrees of freedom. Native neutrino energy and the apparent
one-half temperature feedback include the copied antineutrinos correctly.
The native ideal energy grid and the separate fixed QED grid still require
domain/resolution checks, independent of the two QED expression defects.

## Canonical reference entropy, state and source

Use the declared native numerical coordinate `q`, with physical
`p=c(t)q`, `c=me/x`, and `T_gamma=c z` in MeV. The upstream grid docstring
does not by itself establish a physical unit for `q`. Export `c` explicitly
and give the units of `c` and the native coordinate in the adapter metadata.

Freeze the source-normalization reference at the start:

\[
s_{\rm ref}(x)=s_0(x_0/x)^3,\qquad
\overline s_{\rm ref}=s_0(x_0/m_e)^3.
\]

The provider interface reference is
`s0=(2*pi^2/45)*10.75*T_start^3`,
`T_start=1.00003*me/0.1`. This is the stated reference normalization, not a
claim that the actual evolving plasma has ideal `g_starS=10.75` or that its
entropy remains unchanged. QED thermodynamics, nonthermal neutrinos, electron
annihilation and parent heating must be documented separately. Do not
silently replace the reference density while retaining the frozen `Y0`.

For each one-helicity neutrino or antineutrino species,

\[
{dY_a\over dq}
= {c^3q^2\over2\pi^2s_{\rm ref}}f_a(q)
= {q^2\over2\pi^2\overline s_{\rm ref}}f_a(q).
\]

The adapter's `state_normalization_density_MeV3` is thus the positive
`s_ref(x)`. The six histories copy the three native occupations to the
matching antineutrinos; they represent an imposed charge-symmetry
approximation, not six independent evolution equations.

Convert the actual pre-mixing, pre-collision source accumulator using

\[
S_{a,q}={c p^2\over2\pi^2s_{\rm ref}}
\left.{df_a\over dt}\right|_{\rm src}
={c^3q^2\over2\pi^2s_{\rm ref}}\,
{(df_a/dx)_{\rm src}\over dt/dx}.
\]

The native parent input is the fixed comoving count
`llp_count=Y0*s0*(x0/me)^3`. Native `n_R=llp_count*exp(-t/tau)*c^3`
then gives `n_R/s_ref=Y0*exp(-t/tau)`. With native primary-muon multiplicity
`N_mu=2*B_mumu`, its existing factor one half gives the desired per-species
source

\[
S_{\nu_e}=S_{\bar\nu_e}=B_{\mu\mu}Y_0
{e^{-t/\tau}\over\tau}cK_e(p),\qquad
S_{\nu_\mu}=S_{\bar\nu_\mu}=B_{\mu\mu}Y_0
{e^{-t/\tau}\over\tau}cK_\mu(p),
\]

with zero pre-mixing tau source. No extra charge factor should be introduced.
The source's frozen mass `m_mu=105.6583755 MeV` differs from the native
rounded constant `105.7`; an actual frozen-source callback must identify
this difference and its executed code, without globally changing unrelated
native constants. Physical endpoint adequacy requires
`q_max*c(t)>=m_mu/2` throughout the actual injection interval. Extending the
endpoint at fixed count can coarsen thermal and collision resolution.

If an instantaneous thermal density `s_th(t)` is instead used, the total
canonical state derivative contains an additional term:

\[
{d\over dt}{dY\over dq}
={c^3q^2\over2\pi^2s_{\rm th}}{df\over dt}
 + {dY\over dq}\left[-3H_s-{d\ln s_{\rm th}\over dt}\right].
\]

Here `H_s=d ln a/dt` is per second. This term cannot be assumed zero during
heating or nonequilibrium evolution. Reference entropy avoids this moving
normalization; it does not erase physical entropy production.

## Exact actual-time half-open gate and the parent tail

For each actual native RHS call, evaluate `g = (0 <= state_t < 18*tau)` from
that call's state. Passing `stopPoint=nextafter(x,+inf)` when `g` is true and
`stopPoint=x` otherwise makes both native `x<stopPoint` branches reproduce
this exact half-open condition for finite `x`. Pass the real parent count in
both lanes so parent gravity is unchanged by the source gate. The fixed
`scaleFactorTime.csv` interpolation is not evidence for this actual-time
condition. The native time origin is zero at its starting state; a physical
age offset, if used, must be declared rather than silently added to the decay
clock. A negative-time evolution is outside the source contract.

Native parent density still decays exponentially when injection and
deposition are gated off. Therefore an extension after `18*tau` loses energy
from the represented parent+plasma+neutrino system. In fixed-reference units,

\[
\dot Q_{\rm missing}/s_{\rm ref}
=M_RY_0e^{-t/\tau}/\tau\quad(t\ge18\tau),
\qquad
\int_{18\tau}^\infty dt\,\dot Q_{\rm missing}/s_{\rm ref}
=M_RY_0e^{-18}.
\]

`exp(-18)=1.522997974471263e-8` is an omitted fraction of the initial parent
rest energy in these units. It is not a fractional total-energy bound,
redshifted radiation bound, abundance error or dark-energy constraint.

Three scientifically distinct choices are possible:

1. End the trajectory at a terminal event `t=18*tau`. The source export at
   the endpoint is zero. Use the left-limit derivative for a terminal local
   conservation diagnostic; no step enters the unsupported continuation.
   The gate-off native derivative at that endpoint is still locally
   inconsistent with exponential parent decay. A single endpoint row has
   zero measure in a continuum integral, but trapezoidal integration of a
   discontinuous source endpoint can have a finite last-panel error.
2. Continue native exponential parent survival and explicitly retain the
   missing sink in the residual. Report an open-system diagnostic with a
   bounded omitted tail; do not call the represented system closed.
3. Freeze surviving parents as a stable pressureless remnant after the
   cutoff, `Y_R=Y0*exp(-min(t,18*tau)/tau)`, and gate all deposition off.
   Passing `llp_count_eff=llp_count*exp(max(t-18*tau,0)/tau)` implements this
   survival with the unmodified native density formula. It is continuous and
   conserves represented parent rest energy, but changes the post-cutoff
   decay model. It requires a declared model/version and overflow controls;
   it is not an undocumented native correction.

The shortest bounded adapter should prefer the first choice. A history ending
before the full source window can establish a local evolution fixture only.

## Independent local and trajectory conservation residuals

Let `R=c^-4*rho` and `P=c^-4*physical_pressure` denote the radiation-rescaled
densities of photons, ideal e±, QED corrections, massless neutrinos and a
pressureless parent. All natural/second time conversions must use the native
`hbar`; native `dt/dx=hbar/(H_natural*x)`.

An independent local total-energy residual is

\[
\mathcal L_x={dR_{\rm tot}\over dx}
-{R_{\rm tot}-3P_{\rm tot}\over x}.
\]

Evaluate the plasma partial derivatives from the declared energy callable
and independently declared pressure; evaluate the neutrino derivative from
the actual saved occupation RHS; analytically differentiate the actual
parent survival. Do not reconstruct an energy derivative only from the
temperature equation's own numerator, because that cancellation is
algebraically enforced even when energy/pressure functions disagree.

For native exponential survival,
`R_R=M_R*llp_count*exp(-t/tau)*x/me`,
`R_R'=R_R/x-R_R*t'/tau`. Define

\[
A_N=2z^3[w^2J+Y+2\pi^2/15+G_{2,2}+G_{3,2}],\quad
B_N=2z^3[wJ+G_{2,1}+G_{3,1}],\quad w=x/z.
\]

The native temperature equation enforces
`A_N*z'+R_nu'-B_N-g*R_R*t'/tau=0`. For an independently evaluated plasma,

\[
\mathcal L_x=(\partial_zR_{\rm pl}-A_N)z'
 +\partial_xR_{\rm pl}-{R_{\rm pl}-3P_{\rm pl}\over x}+B_N
 -(1-g)R_Rt'/\tau.
\]

This decomposes thermodynamic mismatch, finite-domain/quadrature mismatch
and the cutoff's missing sink. A useful dimensionless normalization is
`x*L_x/R_total = [rho_dot+3H_s(rho+P)]/(H_s*rho)`; always save the signed
unscaled residual and each component too.

A trajectory check independently computes

\[
\mathcal C(x)=R_{\rm tot}(x)-R_{\rm tot}(x_0)
-\int_{x_0}^{x}du\,{R_{\rm tot}(u)-3P_{\rm tot}(u)\over u}
=\int_{x_0}^{x}du\,\mathcal L_u.
\]

Use actual accepted/dense-output states, endpoint handling and documented
quadrature, then refine trajectory steps and residual quadrature separately.
The equivalent physical check is
`Delta(a^3*rho)+integral(P*d(a^3))=0` for a represented closed system.
Radiation-rescaled energy `R` itself need not be constant during electron
annihilation or pressureless-parent evolution. A total continuity check alone
does not establish microscopic collision accuracy, spectral convergence or
BBN correctness: the photon equation can absorb a numerically wrong
neutrino energy transfer while preserving this scalar balance.

## Executed local evidence

`qed_identity_review.py` calls the literal native QED functions at predeclared
`(x,z)=(0.1,1.00003),(1,1.1),(4,1.4)`, first with default QED81, then with
declared QED161/321 on the same `[0.01,20]` interval. It preserves all native
formulas and constants. Five-point finite differences at `h/z=0.001,0.0005`
agree with complex-step derivatives to at most `1.4e-15` absolute over the
declared grid, while the native derivative differs substantially:

| `(x,z)` | native `dP2/dz` (QED81) | derivative of native `P2` | relative difference |
|---|---:|---:|---:|
| `(0.1,1.00003)` | `-0.01750522242` | `-0.006327973727` | `1.766323499` |
| `(1,1.1)` | `-0.01568300359` | `-0.006408822651` | `1.447095893` |
| `(4,1.4)` | `-0.005645358886` | `-0.003841570761` | `0.469544423` |

The difference persists on refined native quadratures. The QED3 native to
same-grid pressure-energy ratio is exactly `(x/z)^2`: about `0.0099994`,
`0.8264463` and `8.1632653` at those three states. Separate independent
Gauss-Legendre240/480 continuum pressure integrals over `u=p/T in [0,80]`
agree closely; these are reference calculations, not silent native repairs.

The downloaded primary paper, Akita and Yamaguchi,
[arXiv:2210.10307v2](https://arxiv.org/abs/2210.10307v2), printed page20,
eqs.2.51,2.53,2.54, confirms both `rho=-P+T*dP/dT` and
`P3=e^3*T*I^(3/2)/(12*pi^4)`,
`rho3=e^3*T^2*sqrt(I)*dI/dT/(8*pi^4)` with the same `I` definition. Its
logarithmic order-e² term is neglected consistently with this native tree
and the paper's temperature equation. The PDF SHA-256 and retrieval URL are
bound in `qed_identity_review.json`.

`conservation_review.py` independently audits the prior saved native n21 RHS
at `x=4,z=1.4,t=1s,tau=10s,M=300MeV,count=1e-5`. It invokes no new native
RHS or collision JIT. Native temperature-equation cancellation is at
roundoff in zero-parent, positive-parent gate-off and gate-on lanes.
With independent pressure-consistent continuum e±/QED thermodynamics, the
gate-on residual normalized to `H*rho` is approximately `6.5353e-4`, while
the positive-parent gate-off residual is approximately `-4.5887e-2` because
parent exponential decay is not deposited. Literal native energy plus the
declared pressure has a much larger residual; the deliberately coarse n21
grid misses much of the ideal-electron thermal energy and is not evidence
about a converged trajectory. Full raw component and decomposition values
are preserved. No numerical tolerance here certifies production physics.

Replay, preserving fresh output paths:

```bash
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  /workspace/shared/dmde-adapter-conservation/qed_identity_review.py \
  --output /tmp/qed-review-replay.json
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  /workspace/shared/dmde-adapter-conservation/conservation_review.py \
  --output /tmp/local-energy-review-replay.json
```

Both scripts refuse an unclean or different upstream HEAD and never overwrite
existing output. The QED receipt records Python/NumPy/SciPy runtime, source
hashes, reference-code hash and declaration. Source before/after snapshots
agree. A replay outside this directory may omit the PDF hash if the paper is
not present alongside the output; the authored saved receipt binds it.

## Useful bounded evolution and stepper controls

A next fixture can use a declared public toy parent abundance and a fixed
grid, with FD initial state, native collisions/QED/mixing active, and the
frozen-source callback instrumented before mixing. Short fixed intervals,
explicit accepted-step histories and `h,h/2` same-state impulses are useful
even when the thermodynamic limitation is retained. Set endpoint-complete
support for the largest actual `x` reached and keep thermal resolution as a
separate requirement. Start from exactly the same state in each control and
do not optimize the toy abundance or time interval after seeing a result.

Required controls are zero parent with source on/off; positive parent with
identical gravity; pre-mixing source suppression only; actual-time states
just below, exactly at and just above `18*tau`; occupation positivity and
finiteness; copied charge histories; `h,h/2` response stability; and independent
energy residual components. Record source-callback invocation, coordinate
conversion, rejected trials and source consumption. The gate toggle changes
both neutrino injection and parent deposition; a source-only toggle is a
different operation. With parent deposition retained, removing the neutrino
source sends the corresponding energy into the electromagnetic plasma via
the native temperature equation.

The full native RHS applies averaged mixing to the source immediately.
Therefore a full-step impulse tends to `M(q,T)*S_pre` as `h -> 0`, rather
than `S_pre` per flavor. Reducing the step cannot fix that difference.
An injection-stage operator impulse can test the actual canonical callback;
the full transport impulse must use its declared mixed expected response or
a separately versioned operator witness. It cannot be relabeled as a
pre-collision/pre-oscillation source certificate.

Passing these controls would establish executed local callback consumption
and bounded evolution under stated assumptions. It would not establish a
full frozen bridge, all eight contract probes, endpoint/threshold convergence,
complete weak rates, nuclear handoff, abundances, `N_eff` precision, or a
microscopic dark-matter/dark-energy mechanism. A late-time dark-energy sector,
its perturbations and structure/lensing predictions remain unspecified.

The companion `thermodynamics/thermodynamics_derivation.md` gives the detailed
ideal/QED derivation and native line references.

## Separately labeled QED component reference

`qed_component_reference.py` exposes
`pressure_consistent_components(x,z,Constants,Momentum_Grid,native_qed)`.
It keeps native `P2`, `I`, `dIdz` and the native finite quadrature, evaluates
the exact analytic `P2` derivative with `pi^4`, and evaluates the paper's
cubic energy with `z^2`. It does not replace any native function, modify a
native constant, or run a trajectory. This makes the two isolated proposed
expression corrections concrete for code review; it does not validate the
full native equation of state or finite-grid temperature derivatives.

`qed_component_reference.json` preserves native and corrected component
values and their differences relative to each corrected component and to
photon energy. At default QED81:

| `(x,z)` | corrected `rho2` | corrected `rho3` | `(native rho2-corrected rho2)/rho_gamma` | `(native rho3-corrected rho3)/rho_gamma` |
|---|---:|---:|---:|---:|
| `(0.1,1.00003)` | `-0.004753389010` | `0.0004251433074` | `-0.01698585224` | `-0.0006396025753` |
| `(1,1.1)` | `-0.005522900009` | `0.0005793309447` | `-0.01058983084` | `-0.0001043713796` |
| `(4,1.4)` | `-0.004550445517` | `0.0006550803058` | `-0.0009990631263` | `0.001856457240` |

The corrected quadratic derivative agrees with complex-step differentiation
of literal native `P2`; each corrected energy agrees with
`z*P_z-P` for its actual pressure, independently checked by complex-step
and five-point finite differences at the declared steps. The original
negative native receipts remain unchanged and are hashed in this separate
reference receipt. The helper is GPL-3.0-only; `COPYING` supplies the GNU GPL3
text matching the upstream license. The authored review Python scripts in
this directory are distributed under the same GPL-3.0-only terms.

Replay the isolated component check to a fresh output path:

```bash
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  /workspace/shared/dmde-adapter-conservation/qed_component_reference.py \
  --output /tmp/qed-component-reference-replay.json
```

The downloaded paper PDF and text are retained only in the local scratch
directory `/tmp/dmde-qed-primary-reference`, outside this review bundle.
Only its citation, retrieval metadata, SHA-256 and equation summaries are
part of the review artifacts.
`PRIMARY_REFERENCE.json` records the pinned v2 citation, first-page version
date, retrieved-byte SHA-256 and the summarized equations, without reproducing
the downloaded paper.
