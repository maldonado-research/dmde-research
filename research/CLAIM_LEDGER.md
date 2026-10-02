# Claim ledger — 1 October 2026

This ledger concerns the public frozen source specification and the separately dated numerical controls. It contains no private scoring protocol or raw archive material. No observational parameters were fitted in these controls.

| Claim | Evidence class and assumptions | What it establishes | What remains open |
|---|---|---|---|
| Published provider bytes and source formulas reproduce | File identity and source-only numerical validation, Python 3.12.14 / NumPy 2.3.5 | 74 provider members, 73 manifest entries, both frozen payloads, and pair geometry pass their public checks | These checks do not execute the production physics chain |
| Six Born processes obey equilibrium reciprocity | Static infinitely heavy nucleons, finite electron mass, massless neutrinos, common-temperature Fermi–Dirac populations, zero chemical potentials | Each reverse coefficient is `exp(-Delta/T)` times its forward coefficient; separate numerical integration checks the result | Recoil, weak magnetism, radiative/QED corrections, chemical potentials, unequal temperatures, and injected distributions require separate treatment |
| Five processes omit inverse beta decay | Quantified reference-scope limitation; the omission was already disclosed in v0.9.20 | The five-process total fails exact thermal detailed balance; a complete total conflicts with its exact five-column sum semantics | This is not a calculated change in helium or deuterium; a revised evidence contract must be versioned separately |
| Detailed balance alone is insufficient | A deliberately clipped quadrature preserves reciprocity while changing absolute rates | A passing equilibrium ratio cannot prove adequate momentum coverage | Threshold, high-energy-tail, and grid-convergence tests remain mandatory |
| Official PRIMAT controls execute | Recorded commits/settings, upstream shipped caches, freshly executed network evolution | A functional Standard Model backend lane with finite/nonnegative final abundances and recorded baryon accounting | The old note's exact settings are absent; no precision error budget, fresh rate derivation, injected case, or independent backend replication is supplied |
| The source-decay sector conserves energy when coupled consistently | Conditional continuity equations below, ordinary GR and nonnegative densities | Parent loss must equal daughter gain in a complete evolving calculation | Reference source integrals alone do not establish full plasma entropy/energy closure |
| The specified decay sector alone does not cause late acceleration | Ordinary matter parent and relativistic daughters, without a separate vacuum or modified-gravity sector | Their total pressure is nonnegative and cannot generate acceleration in the usual Friedmann equation | A complete DMDE dark-energy sector and its background/perturbation predictions remain unspecified in the public source package |
| Cosmological viability remains untested | No production source-to-transport-to-weak-rate-to-BBN outputs or observational likelihood in this supplement | No supported preference over established alternatives can be reported | Expansion history, abundances, CMB, matter power, structure formation, and lensing require a specified model and explicit comparison |

## Conditional conservation and acceleration check

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
