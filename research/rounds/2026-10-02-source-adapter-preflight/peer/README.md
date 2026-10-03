# Independent component and runtime peer review — 2 October 2026

This AI-assisted review reads the authored runtime adapter and its public
fixed-state receipts. It imports neither the runtime producer, native physics
modules nor provider validators for its independent arithmetic. It reads no
private archive or blinded NPZ, performs no new native RHS or trajectory, and
changes no producer/native output. A separate worker tests the QED helper
from a copied location. No raw primary PDF is included.

## Conclusion and evidence boundary

The runtime adapter correctly implements its declared fixed-reference entropy,
copied neutrino/antineutrino state map, source multiplicity, physical-momentum
Jacobian, source-only toggle and half-open actual-time gate for the evaluated
states. The measured native RHS consumes the captured physical callback with
the predicted mixed coefficient. The literal infinitesimal per-flavor
comparison to the pre-mixing source fails as reported. This is a useful
local operator diagnosis, not a completed bridge or finite-step certificate.

The actual native pre-mixing `df_nudx` accumulator is **not directly
instrumented**. The captured `phi` arrays are actual callback returns. The
exported canonical pre-source arrays multiply those captures by the declared
normalization, independently checked here. The actual consumption witness is
the paired full native RHS difference after mixing. It should not be renamed
as a direct pre-mixing production-accumulator export. Measured `dt/dx` makes
the coefficient check conditional on native Hubble/time evaluation; it does
not independently validate the native QED energy density.

The reviewed final wrapper SHA-256 is
`5bb1ab652581ff07db3cca9ea3bce697b717253719df3ca711246f0ca0e9dd18`.
Current wrapper, final executed snapshot and predeclared wrapper hash agree.
The pinned native RHS SHA-256 is
`e285d33e4ab0f823593a850701be1f90a5ec12c3685834cac68372457ccbaad6`;
the native commit is `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`.
`runtime_peer_review.json` records all 21 native hashes, producer manifest
hashes and independently derived metrics. The current native checkout is
clean and all saved native bytes agree.

## Independent arithmetic replay

`review_runtime_receipts.py` independently transcribes the frozen Michel
polynomials in `u=2p/m_mu`, builds explicit PMNS entries from the pinned
public constants, and subtracts the actual saved source-on/off RHS vectors.
It uses the declaration and actual occupations/callback capture as inputs,
not the producer's reconstructed source arrays as expected answers. All
required checks pass in `runtime_peer_review.json`.

The declared reference gives `T_ref=5.11014229967 MeV`,
`s0=629.2520994400936 MeV^3`, `C0=s0*(x0/me)^3=4.715902064019412`,
`llp_count=4.715902064019411e-6`. At `x=4`,
`s_ref=0.009832064053751465 MeV^3`. The state map is
`J_a(q)=q^2*f_a/(2*pi^2*C0)` for each one-helicity charge species.
With branch `N_mu=2B=0.8`, native charge factor one half, and
`c=me/x`, the pre-mixing source is
`S_a=B*Y0*exp(-t/tau)/tau*c*phi_a`. The measured native derivative uses
seconds through the actual `dt/dx`; no additional `hbar` or charge factor
belongs in this canonical conversion.

At the declared `x=4,z=1.4,t=1s,tau=10s` fixture:

- Independent mixed source consumption error is `6.6908591e-16` relative
  to the expected mixed peak; flavor-sum error is `8.8617428e-16` relative
  to the pre-source peak.
- The literal unmixed per-flavor peak mismatch is `0.5803471906670695`,
  above the stated `0.005` comparison ceiling. Pre-source tau is exactly
  zero; the actual mixed tau peak is `8.79391529235806e-11` in canonical
  yield per native-q unit per second.
- Source-only `delta(dt/dx)=0` exactly, while
  `delta(dz/dx)=-0.00014245175195775478`. Source suppression retains parent
  loss and redirects neutrino energy to the plasma. Entire native gate-off
  is a distinct control: it also suppresses parent deposition.

These are fixed-state infinitesimal RHS quantities. No finite `h,h/2`
production step was executed, and this peak comparison is not the full
contract's weighted-L1/moment/selected-time stepper validation. For a
consistent unsplit stepper, the limiting response is `M*S_pre`; reducing a
step cannot make its per-flavor limit equal to `S_pre`. A separately authored
source substep or split scheme remains a distinct, untested option. This
mismatch does not establish that flavor mixing itself is physically wrong.

Raw boundary arrays confirm callback count one at `t=0` and at the immediately
representable left neighbor of `180s`, and zero at `180s` and its right
neighbor. Small-x/late-time and larger-x/early-time cases follow state time
rather than x. Closed-gate on/off vectors are bitwise equal. Negative time
is rejected before the native RHS; no negative-time physical evolution is
claimed. Zero-parent source on/off vectors are bitwise equal.

N65 is deliberately coarse: the q cell width is about `6.62`, so this fixture
does not resolve the thermal bulk. Endpoint completeness and exact callback
support on these nodes do not certify continuum source moments, collision
accuracy or thermal transport convergence. The constant comoving reference
is appropriate for the prescribed yield; it is not evolving thermal entropy.
Copied charge histories impose symmetry rather than independently evolving
six species. Scalar-global equality is limited to the globals recorded by
the producer; source inspection additionally checks the intended runtime
catalog replacement. It is not general tamper-proof introspection.

## Preserved failures and execution claims

Every member hash in both the first and final producer artifact manifests
matches the actual files. The first wrapper snapshot has SHA-256
`ad03f30916b90e2265f9ea0e85d2c390fd327582aa61b3676f29151307d3a933`.
Its serialization failure exits with supervisor return code1 and retains
stderr, vectors, source captures and a **malformed 572-byte result JSON**.
That partial file is failed evidence, not a usable physics result. The final
wrapper serializes before exclusive file creation and casts the NumPy boolean
explicitly. Scientific declarations and the four reviewed state/RHS/source
CSVs are byte-identical across the two executions; the final receipt uses
more precise infinitesimal terminology.

The saved CLI controls support refusal of `-O`, `-OO`, `PYTHONOPTIMIZE`, refusal
of an existing output, and an atomic fresh-directory race with one winner.
Actual serialization failure is demonstrated; controlled native failure,
process launch failure and timeout were not executed here. Their nonzero
exit branches are source-inspection findings. A source-snapshot failure in
the supervisor's `finally` can itself interrupt later log/receipt writes;
therefore a universal promise that every possible failure has complete
receipts is stronger than the tested evidence. No such failure was observed.

The reviewer initially transcribed `cos(2theta)` with `arccos(sin theta)`;
the pinned native constants use `arccos(cos theta)`. That reversed sign caused
a false mismatch in the first independent draft. The corrected derivation
uses `1-2*sin(theta)^2`. The failed reviewer source/receipt is preserved and
explicitly labeled under `reviewer-transcription-error`; it is neither a
failed producer run nor negative physical evidence about the adapter.

## Copied QED helper CLI

The separate [portability review](portability/README.md) executes an unchanged
copy from another directory with working directory `/tmp`, empty `PYTHONPATH`
and explicit `--source` for the pinned native checkout. All 20 portability
checks pass. All nine QED component observations match exactly; the full
component receipt differs only in timestamp. Copied inputs, original review
inputs and native source remain unchanged.

The minimum runtime siblings are `qed_component_reference.py`,
`conservation_review.py`, `qed_identity_review.py`, and
`qed_identity_review.json`; retain `COPYING` for GPL distribution. No local
RHS fixture, local conservation receipt, PRIMARY_REFERENCE metadata or raw
PDF is needed. The peer receipt fills provenance limits of the original CLI:
it verifies loaded helper paths and utility hashes, validates the original
negative receipt against source identity, and checks native cleanliness after
the process exits. Embedded execution in a contaminated Python process has
different import/global assumptions and was not certified.

This isolated helper validates the two corrected QED component pressure
identities only. No full equation of state, closed trajectory, weak-rate/BBN
handoff, abundance, late-time dark-energy dynamics or structure/lensing model
is established. Native QED defects and the post-cutoff exponential parent
with no deposition remain relevant limitations of literal native evolution.

Replay the peer arithmetic with a fresh output path:

```bash
/workspace/shared/dmde-upstream/nudec-venv/bin/python -B \
  /workspace/shared/dmde-adapter-component-peer/review_runtime_receipts.py \
  --bundle /workspace/shared/dmde-adapter-runtime \
  --source /workspace/shared/dmde-upstream/nudec \
  --output /tmp/runtime-peer-review-replay.json
```
