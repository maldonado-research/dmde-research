# Independent adapter design review

Scope: the public frozen provider specification and the official Nudec commit
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`; no blind payload, private input,
weak-rate trajectory, nuclear network, abundance or observational likelihood.
This is a separate internal review prepared with AI assistance, not external
peer review. The upstream source is read only.

## Reference entropy and occupation conversion

Let `x=a*m_e`, `q=a*p`, `c=m_e/x`, and fix the convention
`s_ref=s0*(x0/x)^3`. For one helicity of one charge species,

`dn/dp=p^2*f/(2*pi^2)` and therefore

`J=dY/dq=c*p^2*f/(2*pi^2*s_ref)`
` =q^2*f/[2*pi^2*s0*(x0/m_e)^3]`.

The last expression is independent of x. An evolving plasma entropy in this
conversion would create an additional derivative and must not replace the
reference entropy. The frozen reference start mapping uses native
`m_e=0.5109989 MeV`, `x0=0.1`, `z0=1.00003`, and `g_starS=10.75`; the different
`0.51099895 MeV` electron mass in the provider weak-kernel validator is a
separate consumer convention.

With `N_mu=2*B_mumu`, the native pre-mixing source gives

`dJ_a/dt=(N_mu/2)*Y0*exp(-t/tau)/tau*c*K_a(c*q)`.

This source is a prescribed production term. It is not the transported state
J, the state derivative including collisions/mixing, or the difference of two
finite-duration coupled evolutions without a small-step check. Tau production
is zero before mixing; transported tau occupation generally need not be zero.

Only three native occupations evolve. The six charge-labelled exports are
aliases of three states under the declared charge-symmetry approximation.
Equal exports confirm that approximation is applied, not that six independent
charge histories were solved. Number and energy sums must count both charges.

## Independent source integrals

Use dimensionless `u=2*p/m_mu` and the frozen densities
`F_e(u)=12*u^2*(1-u)`, `F_mu(u)=2*u^2*(3-2*u)` on `[0,1]`.
For physical lower/upper limits `L,U`, define
`l=max(0,2*L/m_mu)` and `r=min(1,2*U/m_mu)`.
If `r<=l`, every source moment is zero. Otherwise

`I_e,k=(m_mu/2)^k*12*[(r^(k+3)-l^(k+3))/(k+3)`
`                         -(r^(k+4)-l^(k+4))/(k+4)]`,

`I_mu,k=(m_mu/2)^k*[6*(r^(k+3)-l^(k+3))/(k+3)`
`                         -4*(r^(k+4)-l^(k+4))/(k+4)]`.

These finite-domain integrals separate truncation from quadrature error.
Full-domain targets are not appropriate as the sole comparison for a clipped
domain. Do not renormalize samples, hide lower-cutoff loss, or interpret a
same-node source identity test as a continuum integration certificate.

An endpoint-complete fixed q domain overcovers the source at earlier x.
The muon-flavor physical endpoint has a nonzero one-sided value; quadrature
across the moving support boundary can converge slowly or irregularly even
when pointwise source identity is exact. Test varying x, lower and upper
limits, and physical cell width separately.

## Cutoff and coupling

The frozen source gate is actual-time half-open `0<=t<18*tau`, with time zero
explicitly at the transport initial state. Probe the exact cutoff, predecessor
and successor, including states whose x would disagree with the native fixed
table cutoff. A reference `x(t)` table is not an evolved time witness.

In upstream code, the gate controls neutrino injection and parent deposition,
while `n_X` in the Hubble density continues exponentially after the gate.
This leaves a post-gate continuity defect. Capping parent survival at
`exp(-18)` after the gate is a coherent declared residual-parent convention;
retaining exponential decay requires an explicitly bounded continuity defect.
The small residual fraction alone is not a final-observable error bound.

A source-only toggle should leave the parent density and deposition fixed in
the same-state RHS comparison. Coupled finite steps can change photons,
collisions and mixing indirectly, so the pre-mixing impulse and the physical
transport evolution must remain distinct evidence with declared purposes.

## Constant consumers

Changing `Constants.mmu` after imports does not alter globals copied by
`from Constants import *`. The actual Michel consumer is `Distributions.mmu`.
`Core.mmu` consumes the native domain formula if Core is used.
`Thermodynamics_ideal_gas.mmu` is consumed by Jmu/Ymu, but those muon EOS
helpers are not called by the main native RHS. Other imported copies should
be listed explicitly as active or inactive consumers.
`Distributions.__pion_neutrino_energy` is cached at import and depends on mmu;
recompute it consistently or declare it unused at zero pion branching.
Overrides must precede the first Numba compilation. Unchanged upstream bytes
and an executed wrapper hash provide provenance, not correctness.

## Scope of a bounded solve

A short, matched zero/small-source solve with real collisions can establish
that the adapter drives a finite transport evolution and retains solver
termination, accepted states, time, photon variable and energy components.
It cannot certify source-window completeness, full time-cutoff traversal,
source time-integral closure, physical quadrature convergence or transport
precision without the corresponding refinements and checkpoints. A source
diagnostic that passes continuum targets on dense grids does not certify a
much coarser transport grid.
