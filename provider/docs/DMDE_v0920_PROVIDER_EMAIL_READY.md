# Subject: DMDE v0.9.20 frozen two-card spectral-BBN execution request

Hello,

Attached is the DMDE v0.9.20 provider packet for two blinded, source-frozen
late-decay cards. This supersedes v0.9.18. No physical card or target changed;
v0.9.20 only closes reproduced source-shape, operator-chain, and five-channel
weak-rate validation gaps.

Please run both blind IDs with momentum-dependent neutrino and antineutrino
transport, collisions, oscillations, direct neutron-proton weak rates, and a
real BBN network. Please also export the required source-on/off stepper witness,
canonical five-process grouping, all-five Born comparison, and BBN consumption
canaries. The canary outputs are diagnostic and must not replace or be mixed
with the baseline physics outputs.

Before returning the package, please run the supplied validators and provide:

- the completed two-row return CSV;
- coarse and fine bridge NPZ/metadata pairs for each blind ID;
- one raw-evidence ZIP for each coarse and fine run;
- the exact backend code/environment/configuration identity and all hashes;
- any patch or adapter needed to reproduce the callable and stepper witnesses.

Please confirm the momentum-coordinate and stopped-muon endpoint convention in
your implementation. Do not add zero-valued direct-neutrino branching columns
if their mere presence changes native maximum-momentum handling.

Please also confirm that the weak-rate quadrature reaches the returned
52.83 MeV stopped-muon tail at late times; a thermal-tail cutoff near a few MeV
is not endpoint-complete. The pair-response design target is approximately
20 ppm repeatability per positive scalar output if sensitivity to an elasticity
of 0.01 at 3 sigma is sought; report the actually achieved repeatability even
if this target is unavailable.

Passing this packet is an execution-consistency result, not a request to endorse
the DMDE hypothesis. If any field cannot be exported natively, please identify
the exact interface limitation before substituting a reconstructed sidecar.

Thank you,

Ricardo Maldonado
