# Validation scope and limits

v0.9.20 establishes machine-checkable consistency among the frozen source,
the all-node source shape, the canonical transported state, source-on/off
stepper replays, returned electron-flavor spectra, canonical weak-process
rates, the declared BBN input, and signed BBN consumption canaries.

It rejects the defined v0.9.18 false-pass classes: finite-moment source
substitution, cutoff-row injection, coarse source-time bias, non-FD initial
shape, irrelevant-node refinement, a source callable disconnected from the
production stepper, common weak-rate rescaling, and a BBN network insensitive
to the declared input file. It also rejects the reproduced v0.9.19 omission
of positron capture, electron capture, and finite-temperature beta blocking,
plus common capture-rate scaling beyond the independent direction-total band.

It still cannot prove that a provider did not fabricate mutually consistent
evidence, that a named executable generated the archive, that collision,
oscillation, QED, radiative, recoil, weak-magnetism, or nuclear corrections are
physically complete, or that one backend is independently correct. Code,
configuration, logs, witness states, and commands remain subject to analyst
review and replay.

The weak-rate sentinel is an audit-only five-column Born envelope. It does not
separately export the inverse three-body `p+e-+nuebar->n` channel and does not
certify backend-specific corrections. The source-only pair geometry result
does not determine the sign or magnitude of any abundance response.

The Standard Model control summary remains advisory unless a provider returns
a full hashed control bridge and raw-evidence pair. It cannot rescue a failed
injected run. A single successful backend remains provisional; stronger claim
states require the separate private two-backend agreement gate.

No production `Y_p`, D/H, or `N_eff` value is bundled or implied.
