# DMDE v0.9.20 public-backend integration audit

## Conclusion

No inspected public codebase satisfies the frozen v0.9.20 evidence contract without modification. The most practical first production-evidence candidate is a transparent GPL integration of a patched `Nudec_LLP_Solver` transport backend with an instrumented `PRIMAT` weak-rate/BBN backend. A first result from that integration must be labeled a production-evidence candidate, not an independent replication.

## Primary route

### Momentum transport: Nudec_LLP_Solver

- Official repository: https://github.com/baugid/Nudec_LLP_Solver
- Inspected commit: `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62`
- License: GPL-3.0

Its native batch fields match the frozen LLP/muon-source mapping closely and it evolves momentum-resolved three-flavor neutrino distributions. Required work remains: export the complete time history, exact source/state mapping, source-on/off stepper witness, coarse/fine grids, and six explicit neutrino/antineutrino occupations or a reviewed charge-symmetry certificate.

The public momentum-domain rule is not endpoint-complete for the frozen cards: it gives approximately `y_max=897.77`, while the v0.9.20 physical-domain gate requires approximately `1756.90`. A low-resolution endpoint-complete smoke run is therefore not a physics result; production work must patch the endpoint and establish momentum convergence.

### Weak rates and BBN: PRIMAT

- Official repository: https://github.com/CyrilPitrou/primat
- Inspected commit: `908028da9426370f2f41ca996503650eef34795a`
- License: GPL-3.0-or-later

A local pure-Python Standard Model baseline executed successfully, giving `Yp=0.24699183580343323`, `D/H=2.435606846544578e-5`, and `Neff=3.0439772985579183`. This only establishes local executability.

The critical integration blocker is high-energy quadrature. PRIMAT's thermal-tail weak-rate integration can truncate at about `7*m_e = 3.58 MeV` when `T_gamma` is about `0.1 MeV`, whereas the stopped-muon neutrino source reaches `m_mu/2 = 52.83 MeV`. The adapter must extend or split the quadrature through the returned transport endpoint, bracket both weak thresholds, and demonstrate convergence. PRIMAT's rate calculation must also be instrumented into the exact five frozen process columns without cache ambiguity.

## Later cross-checks

`FortEPiaNO` is the strongest inspected route for a later momentum-dependent QKE/oscillation cross-check, but it needs a new stopped-muon source and a Fortran toolchain. `PArthENoPE`, `PRyMordial`, and `LINX` are useful later abundance or rate cross-checks, but none closes the transport-to-five-process chain as supplied.

## Recommended execution order

1. Pin the two primary repositories and record exact source/environment hashes.
2. Run an unblinded integration spike; do not use the frozen cards first.
3. Patch the transport endpoint and export the full history, canonical state map, and source-stepper witnesses.
4. Extend the weak-rate quadrature to the transport endpoint and export all five process columns.
5. Pass the Standard Model replay, the four BBN consumption canaries, and every v0.9.20 adversarial test.
6. Ask both maintainers to review the source semantics, neutrino/antineutrino symmetry, process decomposition, and high-energy quadrature.
7. Only then run both frozen cards at coarse and fine resolution.

Nothing in this audit is a DMDE abundance prediction.
