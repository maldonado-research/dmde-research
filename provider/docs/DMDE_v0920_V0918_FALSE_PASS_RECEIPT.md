# v0.9.18 causal-chain false-pass receipt

## Reproduced class

Starting from the frozen v0.9.17 4Q7N coarse/fine software fixtures, the
history was upgraded to the exact v0.9.18 source-RHS schema. Then:

1. all six evolved distributions at every time were replaced by the same
   equilibrium Fermi-Dirac distribution, erasing injection and flavor
   response; and
2. every total and process-column neutron-proton rate was multiplied by 1.5.

The raw weak-rate and BBN-input CSVs were changed to the same scaled arrays and
the bridge hashes were updated. Both bridges passed v0.9.18 with
`allow_synthetic=False`, and their refinement comparison also passed.

Key machine metrics were:

- source RHS maximum `k=0..5` relative error: `7.4495189568e-4`;
- weak-rate integral and local-history refinement deltas: `0`;
- maximum spectral-moment L1 difference: `1.291714985e-4`;
- maximum spectral-moment global difference: `1.145698382e-6`;
- late median `lambda_np*tau_n`: `1.5000826312`, inside the old `0.5..2` gate.

Separately, nonnegative six-spike electron- and muon-flavor sources reproduce
the first six Michel moments to `2.853e-10` and `1.09e-13`, while their
normalized weighted-L1 distances from the canonical shapes are `1.9764` and
`1.9681`. An arbitrary spike at exactly `t=18 tau` was also outside both old
source masks.

These are validator counterexamples, not physical alternatives and not an
allegation about any external provider.

## v0.9.20 rejection

v0.9.20 adds all-node source L1/CDF checks, an explicit half-open cutoff,
actual time-integrated RHS closure, initial FD shape checks, canonical state
mapping, paired source-on/off production-stepper responses at `h` and `h/2`, an
exact five-process weak-rate ontology, independent all-five Born sentinels, a
late neutron-decay normalization gate, and a signed BBN-consumption canary.

The frozen payload bytes, source identities, branch assignments, and private
scorer are unchanged.
