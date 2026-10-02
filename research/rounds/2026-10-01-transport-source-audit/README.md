# Transport-source diagnostic round — 1 October 2026

**Result:** the pinned public Nudec backend can execute its native stopped-muon
emitter and a local system RHS with real compiled collisions. Its shipped source
domain, constants, cutoff and evidence interface still need an explicit adapter.
No transport trajectory, nonthermal weak-rate history, injected abundance or
observational prediction was calculated in this round.

Ricardo Maldonado's research program; calculations and separate internal review
prepared with AI assistance. This is not external peer review. All inputs are
public source/specification files and declared diagnostic fixtures. No private
archive files or personal documents were copied. The frozen v0.9.20 provider and
release artifacts are unchanged.

## Question and fixed inputs

Can the official Python backend supply a faithful, reproducible starting point
for the source-to-transport bridge? The upstream dependency is
[baugid/Nudec_LLP_Solver](https://github.com/baugid/Nudec_LLP_Solver/tree/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62),
commit `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`. Static inspection records all
21 tracked source-file hashes. Runtime diagnostics use Python 3.12.14,
NumPy 2.3.5, SciPy 1.16.3, Numba 0.63.1 and llvmlite 0.46.0 in a separate
environment. The continuum receipt originally used SciPy 1.17.0; independent
replay with 1.16.3 gives identical numerical fields.

The emission fixture fixes `x_stop=4`, `x=nextafter(4,0)`, native `q_min=0.01`,
and 65, 129, 257, 513 and 1025 uniform nodes. It compares the shipped upper-bound
formula with a physical-endpoint-complete bound, without renormalizing samples.
Each grid executes in a fresh process because Numba captures grid globals.
The exact source moments through fifth order and threshold landmarks are
references. The local RHS fixture uses 21 nodes, `x=4`, `z=1.4`, `t=1 s`,
parent mass 300 MeV, lifetime 10 s, native comoving count `1e-5`, primary-muon
multiplicity `N_mu=0.8`, and zero other multiplicities. It is deliberately too
coarse to establish transport accuracy. No observational parameters are fitted.

## Evidence and negative results

* **Native runtime:** the actual emitter and system RHS return finite arrays.
  The collision routine records a real Numba nopython signature. The zero-parent
  on/off gate vectors are bitwise equal; a positive parent changes the neutrino
  and photon-temperature RHS. Recording wrappers return the original source
  callable's unchanged values. There is no collision, mixing or thermodynamic
  mock. The native gate changes both injection and parent-energy deposition;
  this is not a source-only production-stepper certificate.
* **Physical domain:** native `p=q*me/x` and `q_max=x_stop*mmu/2` give a limiting
  maximum of 27.006291865 MeV, compared with the native 52.85 MeV endpoint.
  The exact local limiting retained number fractions are approximately
  0.329177109 and 0.198680349; retained energy fractions are 0.201550991 and
  0.106288561 for electron and muon flavor. Refining a fixed clipped domain
  converges to those deficient moments. These are `x -> x_stop^-` limits;
  injection is off at the exact stop row.
* **Endpoint rounding:** on the declared complete-domain fixture the terminal
  physical momentum is `52.85000000000001 MeV`, one floating-point step above
  the native endpoint. Native support masking therefore removes the nonzero
  muon-flavor endpoint sample. Its quadrature error decreases with refinement;
  fifth-moment/full-target is about 0.997869374 at 1025 nodes. A successful
  callable or an extended domain does not itself certify numerical precision.
* **Source identity:** the native muon mass is 105.7 MeV rather than the frozen
  105.6583755 MeV. Full continuum moments can satisfy a loose moment tolerance
  while the normalized continuum shape L1 discrepancies, about 0.000997 and
  0.001575, exceed the frozen `5e-4` source-shape threshold. These are continuum
  comparisons, not a completed finite-grid bridge validation. Constants must
  be mapped explicitly rather than relabeling the native result.
* **Weak integration domain:** the PRIMAT Python/C cutoff is an electron
  momentum, with incoming neutrino energies obtained from electron energy
  minus/plus the nucleon mass splitting. At physical photon temperature
  0.1 MeV the static incoming ceilings are 2.3199758672 and 4.9066405872 MeV.
  The bundled Mathematica implementation has a different low-temperature
  floor. The recorded zero-blocking Born capture averages are source-shape
  proxies, not occupied-state rates or abundance changes.

The separate review also integrates a **reference-table proxy** for the decay
history. Using the shipped reference `x(t)` table rather than an evolved
injected background gives about 0.13035% total neutrino-energy upper-domain
clipping loss. Its generation settings are not supplied; the proxy does not
integrate the tiny omitted interval below the probe's `q_min`.
Independent integration and table-interpolation checks reproduce this proxy.
It illustrates why a large instantaneous final deficit does not imply the same
fraction lost throughout the history. It does not determine the loss, energy
closure or abundance response of a production calculation.

The first local RHS receipt mislabeled the native input `0.4` as primary-muon
multiplicity `0.8`. Native code actually accepts the primary multiplicity
directly and applies its own neutrino/antineutrino factor one half. The raw first
receipt and an explicit erratum are retained. Corrected fresh receipts use
native input `0.8`; the numerical emission diagnostics are unaffected. The
first run did not snapshot its wrapper bytes, a provenance limitation recorded
alongside the error. Later corrected runs identify their executed wrappers.

## Records and reproduction

* [Static source audit](source-audit/SOURCE_CAPABILITY_AUDIT.md) and full pinned
  file/citation provenance establish inspected code capabilities and gaps.
* [Continuum diagnostic](coverage/README.md) gives exact Michel moments,
  independent adaptive integration, capture proxies and falsifying controls.
* [Native probe](native-probe/README.md) supplies the actual commands, raw
  samples, refinements, RHS vectors, JIT evidence, corrections and CLI checks.
* [Separate skeptical review](review/REVIEW.md) supplies independent arithmetic,
  constant/coordinate checks and the explicitly limited history proxy.

The top-level hash manifest records the reviewed dossier bytes. Replays must
write new paths under ignored `generated/` or another declared scratch location,
and must preserve historical receipts. Native probe code is explicitly
GPL-3.0-only, with upstream attribution and the license in its own directory;
no external solver implementation is bundled or relicensed. The other authored
research files retain the repository's stated licensing.

[Reproduction commands](REPRODUCING.md) distinguish canonical manifest checks
from deliberately retained errors. The [public-copy replay](public-copy-replay/MATCH_RECEIPT.json)
executes all 11 native jobs from the published candidate code and exactly
reproduces 16 raw numerical files. It identifies the executed wrapper for this
repeat; the first run's wrapper provenance gap remains preserved.

## Next gate and interpretation

The transport-capability queue item is partly demonstrated, with its adapter
requirements still open. Next implement and review an explicit constant and
coordinate map, endpoint-aware momentum quadrature, pre-mixing source export,
reference-entropy convention and actual-time cutoff. Then run a matched
zero/small-source trajectory, check solver termination, retain every accepted
step and energy component, and refine domain, momentum resolution and step size
independently. A complete six-process rate adapter and instrumented nuclear
consumption follow only after those checks.

These calculations derive useful standard source integrals and expose numerical
limitations. They do not establish new physical mathematics, a new DMDE mechanism
or support over ΛCDM. The ordinary dust-parent/radiation-daughter sector alone
still cannot accelerate expansion in GR. The dark-energy sector, conserved
background and perturbations, structure formation, lensing and observational
likelihood comparisons remain unspecified or unexecuted. This methods round
does not create a new Zenodo release.
