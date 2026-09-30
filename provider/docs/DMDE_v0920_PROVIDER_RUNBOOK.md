# Provider runbook

1. Verify the provider ZIP and the two frozen payload hashes.
2. Confirm the native momentum convention, endpoint coverage, muon
   multiplicity, density normalization, and absence of charged-pion injection.
3. Run a matched coarse/fine pair for each blind ID. Both time and momentum
   resolution must improve in the protected source and weak-freezeout windows.
4. Export the v0.9.20 bridge arrays and metadata directly from the production
   state, source, stepper, and weak-rate callables.
5. Produce the eight source-on/off stepper probes at `h` and `h/2` without
   changing any configuration field except the documented source toggle.
6. Extend and convergence-test weak-rate momentum quadrature through the full
   returned transport endpoint. Map native neutron-proton reactions to the
   five canonical process groups and resolve both `Delta_np-m_e` and
   `Delta_np+m_e`.
7. Run the baseline BBN replay from the exact exported rate input, then the
   four diagnostic `1%`/`0.5%` single-rate canaries in the fixed temperature
   window. Keep every canary output separate from the baseline result.
8. Build each raw-evidence ZIP with exact bridge copies, code/environment,
   configurations, commands, logs, rate and abundance histories, operator
   receipt, canary inputs, consumption witness, final outputs, and manifest.
9. Run deep payload, bridge, raw-evidence, refinement, and complete-return
   validation. Return nothing as production if any mandatory gate fails.

Do not infer blind labels. Do not reuse the rejected coarse dry-run values. Do
not replace spectral transport with integrated energy injection.
