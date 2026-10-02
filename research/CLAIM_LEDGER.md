# Claim ledger — 2 October 2026

This ledger concerns the public frozen source specification and the separately dated numerical controls. It contains no private scoring protocol or raw archive material. No observational parameters were fitted in these controls.

| Claim | Evidence class and assumptions | What it establishes | What remains open |
|---|---|---|---|
| Published provider bytes and source formulas reproduce | File identity and source-only numerical validation, Python 3.12.14 / NumPy 2.3.5 | 74 provider members, 73 manifest entries, both frozen payloads, and pair geometry pass their public checks | These checks do not execute the production physics chain |
| Six Born processes obey equilibrium reciprocity | Static infinitely heavy nucleons, finite electron mass, massless neutrinos, common-temperature Fermi–Dirac populations, zero chemical potentials | Each reverse coefficient is `exp(-Delta/T)` times its forward coefficient; separate numerical integration checks the result | Recoil, weak magnetism, radiative/QED corrections, chemical potentials, unequal temperatures, and injected distributions require separate treatment |
| Five-process reference omits inverse neutron decay (`p + e- + anti-nu_e -> n`) | Quantified reference-scope limitation; the omission was already disclosed in v0.9.20 | The five-process total fails exact thermal detailed balance; a complete total conflicts with its exact five-column sum semantics | This is not a calculated change in helium or deuterium; a revised evidence contract must be versioned separately |
| Detailed balance alone is insufficient | A deliberately clipped quadrature preserves reciprocity while changing absolute rates | A passing equilibrium ratio cannot prove adequate momentum coverage | Threshold, high-energy-tail, and grid-convergence tests remain mandatory |
| Official PRIMAT controls execute | Recorded commits/settings, upstream shipped caches, freshly executed network evolution | A functional Standard Model backend lane with finite/nonnegative final abundances and recorded baryon accounting | The old note's exact settings are absent; no precision error budget, fresh rate derivation, injected case, or independent backend replication is supplied |
| Pinned Nudec source and local RHS execute | [Transport-source round](rounds/2026-10-01-transport-source-audit/README.md), declared unblinded grids and matched local states, actual native emitter/collisions | Executable source interface and coupled local response; clipped support and an endpoint rounding error are measured with raw evidence and independent review | No transport trajectory, canonical bridge, production-stepper witness, conservation history or nonthermal abundance prediction is supplied |
| Native constants and quadrature need an adapter | Exact continuum moment/shape comparisons and inspected physical coordinate maps; Oct 2 callback/reference-map fixtures | Loose moment agreement can miss a source-shape mismatch; fixed-domain refinement cannot recover missing support; explicit source and transport mass roles now exist | Full-history endpoint/quadrature adequacy, thermal corrections, evolved-time domain proof and full-domain weak-rate integration remain unresolved |
| Exact frozen callback and canonical source map execute locally | [Oct 2 preflight](rounds/2026-10-02-source-adapter-preflight/README.md), exact source `m_mu=105.6583755`, retained native transport/EOS/collision masses, declared comoving reference entropy | Callback nodal identity, charge-symmetric six-species state/source mapping, actual pre-mixing callback capture and wrapper normalization and half-open actual-time gate are demonstrated on fixed-state RHS fixtures | No accepted-step history, six independent transported species, full EOS closure, trajectory or nonthermal abundance prediction is supplied |
| Sampled source quadrature passes do not establish full-grid transport | Native uniform grid/weights, source-only endpoint-phase scans and independent numerical replay | N3001 fails the broader short-window phase scan; N4001/N8001 pass 1,001 sampled coordinates; the tested full reference-domain ladder fails throughout | Continuous-phase/source-history adequacy, native-weight conditioning, conservative collision discretization and collision runtime remain open; no dense collision or trajectory success is inferred |
| A mixed stepper is not a literal pre-mixing source witness | Native immediate source mixing and separately recorded local mixing controls | A nonzero tau response can arise immediately from mixing even though the canonical pre-mixing tau source is zero | A genuine split source-operator witness or separately versioned mixed-response contract is required; the frozen provider contract remains unchanged |
| Fixed-state energy bookkeeping is not full EOS conservation | Bounded local source/RHS evidence and independent thermodynamic review | Local source energy normalization and bookkeeping can be checked without evolving a background | A separately versioned pressure-consistent EOS/thermal-correction audit and complete parent/plasma/neutrino continuity history are required before a trajectory or conservation claim |
| Final instantaneous deficits differ from history loss | Exact local Michel integrals; separately reviewed reference-table decay-weighted upper-domain proxy | Large final-domain clipping is compatible with a much smaller history-weighted proxy loss | The shipped reference table's generation settings are absent; actual injected-history losses and abundance effects remain uncalculated |
| The source-decay sector conserves energy when coupled consistently | Conditional continuity equations below, ordinary GR and nonnegative densities | Parent loss must equal daughter gain in a complete evolving calculation | Reference source integrals alone do not establish full plasma entropy/energy closure |
| The specified decay sector alone does not cause late acceleration | Ordinary matter parent and relativistic daughters, without a separate vacuum or modified-gravity sector | Their total pressure is nonnegative and cannot generate acceleration in the usual Friedmann equation | A complete DMDE dark-energy sector and its background/perturbation predictions remain unspecified in the public source package |
| Cosmological viability remains untested | No production source-to-transport-to-weak-rate-to-BBN outputs or observational likelihood in this supplement | No supported preference over established alternatives can be reported | Expansion history, abundances, CMB, matter power, structure formation, and lensing require a specified model and explicit comparison |

## Conditional conservation and acceleration check

The Oct 2 independent QED audit identifies two concrete native expression
defects: the final `dP_2dz` product needs `pi^4` in its denominator, and `rho_3`
needs `z^2` rather than `x^2`. The isolated pressure-consistent component
reference passes complex-step and finite-difference identity checks on the
declared state/grid ladder. It does not replace or validate a full EOS,
heat capacity, background evolution, or observational prediction.

For a nonrelativistic decaying parent `R` and relativistic daughters `r`, with decay rate `Gamma` and natural units:

```text
dot(rho_R) + 3 H rho_R = -Gamma rho_R
dot(rho_r) + 4 H rho_r = +Gamma rho_R
```

Summing gives total stress-energy conservation. For ordinary general relativity and no extra sector,

```text
ddot(a)/a = -(4 pi G/3) [rho_R + 2 rho_r] <= 0.
```

This conditional result limits what this early decay sector can establish; it does not exclude unspecified stable dark matter, vacuum, or modified-gravity extensions. An effective equation of state assigned to one receiving component must not be substituted for the physical total pressure. A short-lived source component cannot be treated as present-day stable cold matter without an additional mechanism.

## Comparison required before claiming physical support

A complete model should compare against a Standard Model/ΛCDM control under matched baryon density, neutron lifetime, nuclear inputs, neutrino treatment, and observational likelihood. Relevant outputs include `Yp`, `D/H`, `Neff`, `H(z)`, the matter transfer function/growth, and lensing potentials. The choice of data, covariance, nuisance parameters, fitted parameters, and held-out predictions must be stated. No claim of a current observational exclusion or preference is made without that calculation and current data access.
