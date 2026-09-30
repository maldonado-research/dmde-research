# DMDE v0.9.20 provider dispatch — five-channel causal-chain gate

This packet supersedes v0.9.18 for external execution. The two blind payloads,
their byte hashes, the frozen model branch, all physical parameters, and the
private v0.9.13 scorer remain unchanged.

v0.9.20 repairs reproduced execution-validity false passes. A v0.9.18 return
could match source moments through fifth order while carrying a nearly
maximally wrong source shape. It could also return source-independent thermal
spectra, multiply every weak rate by a common factor, copy those values into
the BBN handoff, and still pass bridge and paired-refinement validation.
An additional v0.9.19 counterexample omitted both charged-lepton capture
channels and used unblocked vacuum beta decay at every temperature while the
full firewall still passed.

The new contract therefore requires:

1. direct all-node Michel-source shape, CDF, support, cutoff, and time-integral
   closure;
2. direct initial Fermi-Dirac shape closure for all six species;
3. meaningful time- and momentum-grid refinement, not only a larger bin count;
4. a source-on/source-off production-stepper witness at eight frozen source
   times, evaluated at both `h` and `h/2`;
5. canonical weak-process grouping plus independently recomputed,
   neutron-lifetime-normalized Born lanes for all five exported processes, a
   10% direction-total lane, and explicit threshold/endpoint refinement;
6. a baseline BBN replay and four small shadow-rate canaries proving that the
   declared rate handoff is consumed by the declared network.

Run both blind IDs. Return the two-row CSV, coarse/fine bridge NPZ and metadata
JSON files, and coarse/fine raw-evidence ZIPs. Run the supplied validators
before returning any result. Do not infer the private labels and do not replace
momentum-resolved transport with an energy-only calculation.

Passing establishes a replayable, internally linked source-to-transport-to-
weak-rate-to-BBN execution chain. It does not establish that the backend is
physically correct, independently replicated, or that DMDE is confirmed.
Production spectral-BBN results remain pending external execution.

The packet also includes a source-only differential-response result. The
frozen pair has `Delta ln(a_nu)=0.008654677649784786` but only
`Delta ln(e_EM)=3.98597101534914e-6`, so its pair direction is a quantified
near-neutrino-axis finite difference. This is a numerical-design result, not a
transport or abundance result.
