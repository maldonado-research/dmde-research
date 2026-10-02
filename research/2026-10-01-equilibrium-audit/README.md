# Six-process Born equilibrium audit — 1 October 2026

This reproducible methods result quantifies the inverse neutron-decay process
already identified as a limitation of the public v0.9.20 five-process contract.
It supplies a separate reference calculation and regression tests. The frozen
provider packet and its published release are unchanged. This is established
detailed-balance physics applied to this project's reference, not new particle
physics, a discovery, a fitted cosmology, or a production BBN prediction.

## Main result

For an electron, positron, neutrino and antineutrino bath with a common
temperature and zero chemical potentials, all three forward/reverse pairs obey
the same detailed-balance ratio. Omitting inverse beta decay breaks the total
ratio by a calculable amount. Adding the missing reference integral restores it.

| Temperature (MeV) | Inverse beta rate (s^-1) | Missing fraction of complete p→n rate | Complete/five-process p→n − 1 |
|---:|---:|---:|---:|
| 5 | 2.48619e-4 | 1.00165e-7 | 1.00165e-7 |
| 0.8 | 1.06136e-4 | 0.00090390 | 0.00090472 |
| 0.3 | 1.15822e-5 | 0.08861585 | 0.09723216 |
| 0.25 | 5.25031e-6 | 0.18273690 | 0.22359616 |
| 0.2 | 1.54448e-6 | 0.37825267 | 0.60837040 |
| 0.1 | 2.67195e-9 | 0.91788143 | 11.17751285 |

The two relative-error columns have different denominators. Large relative
errors in the exponentially suppressed late reverse rate do **not** establish
large abundance errors. No helium, deuterium or effective-neutrino-number
response is calculated here.

## Equations and assumptions

Let Δ = m_n − m_p = 1.29333236 MeV, m_e = 0.51099895 MeV, and let p denote
the massless neutrino energy. The assumptions are infinitely heavy unpolarized
nucleons, finite electron mass, a common Born normalization, and Pauli blocking.
The example neutron lifetime is an input, τ_n = 879.4 s, with no fitted parameters.
Radiative, recoil, weak-magnetism, finite-nucleon-mass and plasma corrections are
absent. For zero chemical potentials,

\[
f_e(E)=[e^{E/T_\gamma}+1]^{-1},\qquad
f_\nu(p)=f_{\bar\nu}(p)=[e^{p/T_\nu}+1]^{-1}.
\]

Define the phase functions (zero outside the indicated domains):

\[
K_+(p)=p^2(p+\Delta)\sqrt{(p+\Delta)^2-m_e^2},\quad p\ge0,
\]
\[
K_-(p)=p^2(p-\Delta)\sqrt{(p-\Delta)^2-m_e^2},\quad p\ge\Delta+m_e,
\]
\[
K_\beta(p)=p^2(\Delta-p)\sqrt{(\Delta-p)^2-m_e^2},\quad0\le p\le\Delta-m_e.
\]

Every rate is A times the integral over dp of the following expression:

| Process | Integrand without A dp |
|---|---|
| ν_e + n → p + e− | K_+ f_ν(p) [1−f_e(p+Δ)] |
| e+ + n → p + ν̄_e | K_- f_e(p−Δ) [1−f_ν̄(p)] |
| n → p + e− + ν̄_e | K_β [1−f_e(Δ−p)] [1−f_ν̄(p)] |
| ν̄_e + p → n + e+ | K_- f_ν̄(p) [1−f_e(p−Δ)] |
| e− + p → n + ν_e | K_+ f_e(p+Δ) [1−f_ν(p)] |
| p + e− + ν̄_e → n | K_β f_e(Δ−p) f_ν̄(p) |

The lifetime normalization is A = 1/(τ_n I_0), where

\[
I_0=\int_{m_e}^{\Delta}E\sqrt{E^2-m_e^2}(\Delta-E)^2\,dE
=\frac{m_e^5}{60}\left[\sqrt{z^2-1}(2z^4-9z^2-8)+15z\operatorname{arcosh}z\right],
\quad z=\Delta/m_e.
\]

The analytic value, 0.05700452626306703 MeV^5, is independently checked against
quadrature. The normalization has units s^-1 MeV^-5.

At T_ν = T_γ = T, the identity f/(1−f) = exp(−E/T) gives, point by point,

\[
\frac{\lambda_{ep}}{\lambda_{\nu n}}
=\frac{\lambda_{\bar\nu p}}{\lambda_{e^+n}}
=\frac{\lambda_{\mathrm{inverse}\,\beta}}{\lambda_\beta}
=e^{-\Delta/T}\equiv r.
\]

Thus, with N the sum of the three n→p rates,

\[
\lambda_{pn}^{(6)}=rN,\qquad
\lambda_{pn}^{(5)}=r(N-\lambda_\beta),\qquad
\frac{\lambda_{pn}^{(5)}}{rN}-1=-\frac{\lambda_\beta}{N}.
\]

This equilibrium relation must **not** be imposed on transported nonthermal
spectra or unequal bath temperatures. Tests explicitly demonstrate those
counterexamples. For arbitrary 0 ≤ f_ν̄ ≤ 1, two valid identities remain:

\[
\lambda_\beta-\lambda_{\mathrm{inverse}\,\beta}
=A\int K_\beta(1-f_e-f_{\bar\nu})\,dp,
\qquad
0\le\lambda_{\mathrm{inverse}\,\beta}\le A\int K_\beta f_e\,dp.
\]

The first expression is a difference of per-nucleon rate coefficients, not the
net neutron-production collision term. Neutron-fraction evolution would require
the population weights: dX_n/dt = (1−X_n)λ_pn − X_n λ_np.

## Consequence for the frozen contract

The old process arrays have three n→p columns and two p→n columns, and require
the columns to sum to the exported direction totals. A genuinely complete
six-process p→n total cannot satisfy that exact identity with only the two
genuine reverse-capture rates. Relabeling or folding inverse beta into another
physical process would change the meaning of the columns.

Separately, the complete reference p→n total exceeds its five-process reference
by 10% below approximately 0.2981757364 MeV in this thermal fixture. That statement
uses the old total-band denominator, λ_pn^(5), and concerns reference integrals.
The validator's history-dependent non-negligibility floor may mask individual
late nodes; it must be considered before inferring an actual validator outcome.
For example, the 0.25 MeV table node has a five-process rate 2.34812e-5 s^-1,
above the roughly 8.49e-6 s^-1 floor generated by this table's 10 MeV peak.
Simply adding a sixth contribution to the total would already fail the exact
process-sum check. This audit does not simulate a full provider-return archive
or claim an unreported production-backend failure.

A future complete contract requires a separately versioned process ontology and
review of all affected schemas, metadata, bridge checks and adapters. This
standalone audit deliberately does not change those published interfaces.

## Reproduction and numerical checks

From the repository root, using the documented Python/NumPy environment:

```bash
python3 -m unittest discover -s research/2026-10-01-equilibrium-audit -p 'test_*.py' -v
python3 research/2026-10-01-equilibrium-audit/equilibrium_audit.py
```

[JSON receipt](outputs/equilibrium_audit.json) and [CSV table](outputs/equilibrium_rates.csv)
record source hashes, constants, package versions and numerical settings.
No private archive inputs are used. Reproduction does not require network access.
An alternate output directory can be supplied with `--output-dir`.

The 13 tests check the analytic normalization, vacuum lifetime, high-temperature
quarter-lifetime beta limit, each reverse pair, the full equilibrium ratio,
omission and clipped-domain negative controls, arbitrary occupations, unequal
temperatures, normalization scaling, invalid inputs and the preserved provider.
Endpoint square roots are removed by quadratic substitutions. Quadrature order
96→192 and tail 60T→80T are varied separately; rate changes are below 2e-14
on this table. Thermal tails beyond either cutoff remain exponentially small
under the stated FD assumptions. These convergence results do not bound
discretization error for arbitrary untested nonthermal spectra.

The frozen provider is run on a separate composite neutrino-energy quadrature.
Its five integrands agree after accounting for its 2.34e-8 relative normalization
offset from a 256-node unsmoothed I_0 quadrature. That tiny offset is recorded,
not presented as a material physics issue.

The clipped-domain negative control is consequential: a deliberately short
10T integration tail biases capture rates while still satisfying detailed
balance. Reciprocity alone therefore cannot certify domain completeness or
absolute accuracy. No claim of new mathematics or precision cosmology follows
from passing these tests.

Public source anchors:
[five-process scope](../../provider/docs/DMDE_v0920_WEAK5_CLOSURE_AND_FALSE_PASS.md),
[frozen code](../../provider/code/dmde_v0920_validate_weak_rate_closure.py),
[broader validation limits](../../provider/docs/DMDE_v0920_VALIDATION_SCOPE_AND_LIMITS.md).
