# Frozen gate and native unsplit mixing

The frozen source-identifying gate is coherent for an exported pre-collision,
pre-oscillation production source. The additional stepper gate is incompatible
with the native **unsplit mixed System_Nudec RHS** as its candidate consumer.
This is not a claim that all physically meaningful split production schemes
are incompatible.

The public `DMDE_v0920_SOURCE_OPERATOR_CLOSURE_GATE.md`, lines 109–120,
requires the pre-collision/pre-oscillation RHS and says paired production-stepper
outputs must agree with that validated RHS. The metadata template, lines 40–44,
identifies the main stepper, source toggle and on-minus-off/step definition.
The validator `dmde_v0920_validate_bridge_bundle.py`, lines 1262–1324,
forms that per-species response, compares electron/muon responses to the
pre-mixing source, and requires both tau responses below `1e-14` of the source
peak. It does not transform the validated source with the transport mixing
matrix before this comparison.

The native RHS `System_Nudecoupling.py`, lines 116–124, constructs the source
and immediately mixes it. At a fixed identical state, all background and
collision terms cancel in a source-only on/off RHS difference, but the source
contribution remains `P*S`, not S. For a differentiable full production step
of duration h, `(J_on(h)-J_off(h))/h -> P*S` as `h -> 0`. Halving cannot remove
an order-one tau contribution from this limit. Holding source-off parent
deposition fixed does not change this conclusion.

An independent executable witness records the actual upstream emitter and
actual mixing matrix on declared public diagnostic points. For
`T={0.05,0.1,0.5,1,5} MeV` and
`p={0.01,0.1,1,10,25,40,m_mu/2} MeV`, the tau fraction of total source ranges
from **0.17399084053 to 0.48955349175**. Independent beta-density source values
match the actual emitter to `7.34e-16` of peak; an independent explicit PMNS
construction matches the actual mixing probability to `3.34e-16` absolute.
The source flavor sum is preserved to numerical precision. These checks
evaluate mixing/source callables; they do not execute collisions or transport.

The probe also records a 513-node example at `x=4,z=1.4`: the mixed tau peak is
`0.502382447356` times the pre-mixing source peak, while the pre-mixing tau
source is exactly zero. Upstream Python source hashes before and after are
identical. Only the emitter's in-memory muon mass is changed for this diagnostic
and that limited override scope is explicitly recorded.

A declared source substep genuinely consumed by an operator-split production
scheme could be compared directly with S. The frozen public text does not
explicitly forbid this interpretation. Such a substep must be documented as
the actual source-stage consumer and reviewed within the production scheme;
an isolated Euler reconstruction that is never used by the real transport
stepper would not establish production consumption. Do not change the frozen
contract or relabel a native full mixed step as a pre-mixing witness.

The final replay artifacts are `frozen_stepper_mixing_probe.py`,
`mixing-guarded-final-review/frozen_stepper_mixing_probe.json`, and
`mixing-guarded-final-review/frozen_stepper_mixing_samples.csv`, with executed script
bytes retained in that result directory. The initial local-path run is also
retained separately. The script was executed with the pinned
Nudec Python environment. This separate internal review was prepared with AI
assistance; it is not external peer review and produces no abundance result.
