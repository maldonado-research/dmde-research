# DMDE v0.9.20 causal-chain repair

## Frozen scope

No source card, payload byte, lifetime, abundance, branching fraction, lattice
assignment, physical branch, observational oracle, or private scoring rule is
changed. The frozen branch remains

\[
n=31\ \text{protected parent}
\rightarrow 2\times n\simeq 32.05/32.06\ \text{sub-pion relay}
\rightarrow e^+e^-,\mu^+\mu^-,
\]

with the `n=35` mediator dark-only and charged-pion injection zero.

## Reproduced v0.9.18 false passes

Two independent counterexamples justify this release.

First, six nonnegative spikes on a 501-node source grid reproduce every Michel
moment from `k=0` through `k=5` to better than `3e-10`, yet have normalized
weighted-L1 distances `1.9764` and `1.9681` from the electron- and muon-flavor
Michel densities. Moment closure alone therefore does not identify the source
shape.

Second, a full bridge can carry the exact frozen source RHS while all six
evolved distributions are replaced by the same equilibrium Fermi-Dirac state.
Multiplying every neutron-proton rate and every matching process column by
`1.5` preserves process sums, detailed-balance ratios, raw CSV linkage, and
coarse/fine convergence. Both v0.9.18 bridge files still pass.

These are validator counterexamples, not DMDE predictions and not allegations
about any external backend.

## New closures

### Source shape and time

At every active time row, the returned electron and muon source arrays are
compared directly with the discrete canonical Michel source on the same nodes.
The weighted-L1 and normalized-CDF ceilings are `5e-4`; a rowwise peak-scaled
residual ceiling is `5e-3`. Support above `m_mu/2` is forbidden. The source is
half-open in time, `0 <= t < 18 tau`; every row at or after the cutoff is tested.

The scalar decay-history integral and the actual two-dimensional source number
and energy integrals must each close at `5e-5`. This restores the demonstrated
historical source-time accuracy and prevents a coarse time grid from consuming
most of the frozen pair's `0.8692%` neutrino-source contrast.

### Initial state and stepper witness

All six initial distributions are compared with the complete Fermi-Dirac shape,
not only its third moment. A canonical state density

\[
g_a(t,q)=\frac{p^2\,dp/dq}{2\pi^2 s_{\rm ref}(t)}f_a(t,q)
\]

is exported for each separate neutrino and antineutrino species. At the nearest
bridge nodes to `t/tau = 0, .25, .5, 1, 2, 4, 8, 16`, the production stepper is
replayed from the exact hashed state with the spectral source on and off, for
steps `h` and `h/2`. The differenced response must converge to the already
validated frozen source RHS in weighted L1 and moments through fifth order.

### Spectra to weak rates

Native weak processes must map to five canonical free-nucleon groups. The
validator independently reconstructs audit-only finite-electron-mass Born
histories for all five exported process columns from the returned spectra. The
normalization is fixed by the declared neutron lifetime. Corrected production
columns remain authoritative for BBN, but each must remain within a
conservative `25%` semantic band of its Born lane and each direction total
within `10%` of the independent sum where the sentinel is
non-negligible. The late free-neutron-decay process must close to `1/tau_n`
within `0.5%`.

### Rates to BBN

The raw archive contains a deterministic replay of the exact baseline BBN
rate-input hash and four diagnostic shadow inputs. Only one rate is increased
inside `1.2 >= T_gamma >= 0.5 MeV`, by `1%` or `0.5%`. The `n->p` shadows must
decrease `Y_p`; the `p->n` shadows must increase it; each doubled perturbation
must have a response ratio between `1.5` and `2.5` and exceed the declared
deterministic noise floor. These shadow outputs are execution canaries only and
are never scored as physics results.

## Scientific basis and boundary

Momentum-dependent neutrino evolution is governed by a Liouville/quantum
kinetic equation whose collision and oscillation terms act on the evolving
density matrix. Full BBN calculations then use the electron-flavor spectra in
the neutron-proton rates and couple those rates to the abundance network. See
Grohs et al., [arXiv:1512.02205](https://arxiv.org/abs/1512.02205), Froustey and
Pitrou, [arXiv:1912.09378](https://arxiv.org/abs/1912.09378), and the modern
Liouville-equation review and code comparison in
[arXiv:2511.04747](https://arxiv.org/html/2511.04747v2).

The v0.9.20 gates test execution linkage and numerical semantics. They do not
independently solve the transport or nuclear equations, certify the physical
corrections chosen by a backend, or replace independent replication.
