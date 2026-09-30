# Clarify momentum convention and support causal spectral-to-BBN replay evidence

We are preparing two blinded late-decay conformance runs using the public
momentum-dependent neutrino solver interface. The source cards are frozen and
inject stopped-muon `nu_e`, `nuebar`, `nu_mu`, and `numubar` spectra below the
charged-pion threshold.

Could the maintainer please confirm:

1. the exact dimension and physical conversion of the maximum comoving
   momentum used for late injection;
2. whether the native muon field is the average number of primary muons per LLP
   decay, so a pair probability maps to `N_mu=2 B_mumu`;
3. how to export the actual pre-collision/pre-oscillation source RHS;
4. which production stepper callable can be replayed from the same state with
   only the spectral source toggled;
5. how the electron-flavor spectra enter the named neutron-proton weak-rate
   callable and its exact five-column process decomposition;
6. how the weak-rate quadrature can be extended through the returned
   stopped-muon endpoint instead of a thermal-tail cutoff; and
7. how to prove that the BBN network consumed the returned rate-history input.

The attached v0.9.20 conformance packet includes validators and test-only
counterexamples. It does not assert an upstream bug or contain a BBN result.
The source-on/off and BBN shadow runs are diagnostic witnesses only.
