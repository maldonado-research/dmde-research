# Source-adapter preflight — 2 October 2026

The exact frozen source now executes through the pinned native Nudec RHS with
an explicit coordinate/entropy map and actual-state-time cutoff. Twelve
fixed-state adapter checks pass. Three independent prerequisites still block
a physical transport trajectory: source-grid adequacy, the production-operator
witness, and consistent QED thermodynamics. This round supplies concrete
negative controls and an isolated pressure-consistent QED component reference;
it does not supply a validated cosmological solution.

## Inputs and assumptions

The official GPL solver is `baugid/Nudec_LLP_Solver` at
`0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`. All 21 tracked upstream files remain
unchanged. The source callback alone uses `m_mu=105.6583755 MeV`; native
transport uses its original `me=0.5109989` and `mmu=105.7`. No global constant
repair is hidden inside the adapter. The native three occupations are copied
to their charge partners; six exported fields do not mean six independent
transport equations.

Physical momentum is `p=(me/x)q`, and photon temperature is `(me/x)z`. The fixed
reference is `x0=.1`, `z0=1.00003`, `g_s_ref=10.75`, with
`s0=(2*pi^2/45)*g_s_ref*(z0*me/x0)^3` and
`s_ref=s0*(x0/x)^3`. The canonical state is
`J=q^2*f/(2*pi^2*s0*(x0/me)^3)`. This reference normalization does not assert
that the evolving physical plasma has conserved ideal thermal entropy.

The local native fixture fixes `B_mumu=.4`, `Y0=1e-6`, `tau=10 s`, parent mass
`300 MeV`, `x=4`, `z=1.4`, and actual time `1 s`. Native primary multiplicity
is `.8`; its existing one-half factor supplies the per-charge source. These
are diagnostic inputs, not fitted parameters or an inferred DMDE model.
The deliberately coarse N65 local grid is uncertified for thermal or source
moments. Source-grid diagnostics use their own explicitly declared settings.
No observational parameters were fitted anywhere in this round.

## Demonstrated results

| Question | Evidence | Result and limit |
|---|---|---|
| Does the real native RHS consume the authored source? | Actual callback captures, saved occupations/vectors, source-versus-zero callback at identical parent/background, independent mixing/coefficient reconstruction | Coefficient agrees to `4.46e-16` relative to the source peak; all 12 adapter checks pass. The internal pre-mixing accumulator is not directly instrumented. |
| Is the cutoff controlled by actual state time? | Zero, left/exact/right `18*tau`, mismatched x/time, and negative-time interface probes | Injection is on immediately below `18*tau`, off at/above it; negative times are rejected before native execution. These are fixed-state probes, not an evolved history. |
| Can the native unsplit RHS witness the frozen pre-mixing source? | Source-only derivative versus declared pre-mixing source | Relative peak mismatch is `0.580347`, above the declared `.005` comparison ceiling; tau response is positive where pre-mixing tau source is zero. No finite-step h/h2 gate was evaluated. A genuinely consumed source substep in an explicitly split method remains a possible route. |
| Is a fixed full-reference grid adequate? | Native-weight source moments through k=5 at six x coordinates | N301/1001/3001/10001 all fail the `.005` source-moment ceiling; worst errors are approximately 82.54%, 26.94%, 3.16%, 5.01%. Refinement is nonmonotonic because a moving, nonzero endpoint changes its phase relative to grid nodes. |
| Does a short-window three-point pass suffice? | 1,001-coordinate phase sweep, separately evaluated with beta/incomplete-beta integrals | N3001 fails at `.00539153`; N4001/8001 pass sampled coordinates at `.00398695`/`.00202978`. This is a finite sample of source moments, not a continuous bound or a collision/trajectory validation. |
| Are native QED energy expressions pressure-consistent? | Complex-step and five-point derivatives at three states and QED grids 81/161/321; primary equations in [Akita–Yamaguchi, arXiv:2210.10307v2](https://arxiv.org/abs/2210.10307v2), page 20 | Native `dP_2dz` uses `pi^2` in its final product denominator where differentiating native pressure requires `pi^4`; native `rho_3` uses `x^2` where pressure thermodynamics requires `z^2`. The isolated corrected component reference satisfies the pressure identities to numerical precision. |

The QED helper neither patches the native EOS nor establishes consistent
heat capacity, ideal-electron quadrature, Hubble evolution or collisions.
No effect on `Neff`, helium, deuterium or observational likelihood is estimated.
Formal cancellation in the temperature equation is insufficient: energy must
also agree with independently evaluated pressure and density derivatives.

The independent review measures a `0.0114882` relative source-moment error on
the actual N65 runtime fixture. It fails the frozen `.005` ceiling even though
its same-node source coefficient is correctly consumed. Both findings are
retained; the local fixture cannot establish source-moment or transport precision.

The gate retains exponentially decaying parent gravity while deposition stops.
Continuing beyond `18*tau` therefore leaves an unrepresented energy sink.
`exp(-18)=1.523e-8` is the omitted fraction of initial parent rest energy, not
a total-energy or abundance error bound. A prospective trajectory should end
at the declared cutoff or specify and account for a different continuation.

## Records, review and reproduction

- [domain/README.md](domain/README.md): source callback and canonical map,
  full-cap ladder, dense endpoint-phase scan, synthetic snapshot arrays,
  collision-grid geometry controls, original serialization failure, and
  hardened executed-wrapper replays.
- [runtime/README.md](runtime/README.md): actual collision-compiled native RHS,
  actual callback captures, paired vectors, boundary probes and preserved
  first serialization failure. This is actual local native-RHS source-consumption evidence;
  the domain snapshots alone do not demonstrate consumption.
- [conservation/README.md](conservation/README.md): independent entropy,
  pressure/energy and cutoff derivations; untouched native negative receipts;
  separately labeled corrected QED components and primary-source metadata.
- [review/README.md](review/README.md) and [peer/README.md](peer/README.md):
  independent computational reviews. These are separate AI-assisted reviews,
  not external scientific peer review.
- [REPRODUCING.md](REPRODUCING.md): fresh-output commands and exact runtime.
  [PUBLIC_COPY_REPLAY.json](PUBLIC_COPY_REPLAY.json) records root replay from
  the actual public paths. [ARTIFACT_SHA256.json](ARTIFACT_SHA256.json) is the
  canonical self-excluding file-identity manifest; run `verify_dossier.py`.
- [PUBLICATION_AUDIT.md](PUBLICATION_AUDIT.md): selected-file privacy, licensing,
  frozen-byte and CI-scope audit. Its receipt precedes inclusion of its own
  note and this link; the final root manifest includes those additions.

Retain failed runs, old executed-wrapper snapshots and later corrections
together. Passing adapter checks describe execution and normalization;
the known physics-gate failures remain failures. The wrappers and component
reference are GPL-3.0-only with license copies. No private archive files,
personal documents, primary-paper PDFs, or private scoring material are in
this dossier. Frozen v0.9.20 provider and release bytes remain unchanged.

## Next gate and physical interpretation

First validate a separately versioned pressure-consistent full EOS and its
derivatives, construct an actual production source-operator witness compatible
with a declared split method or a new versioned contract, and establish a
conservative momentum grid with independent thermal/source/collision budgets.
Only then attempt matched zero/small-source evolved histories and independent
domain/time/momentum refinement. Six-process weak rates and demonstrated
nuclear-network consumption follow later.

This round makes no dark-matter or dark-energy discovery claim. The existing
ordinary-GR pressureless-parent/radiation-daughter sector cannot itself cause
acceleration. A covariant dark-energy sector, production mechanism, background
and perturbations, structure/lensing predictions, and comparison to matched
Standard Model/ΛCDM controls and observational data remain open. Component
corrections and numerical maintenance are not grounds for a new Zenodo release.
