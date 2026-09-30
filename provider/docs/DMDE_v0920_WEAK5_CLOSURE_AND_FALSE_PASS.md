# DMDE v0.9.20 five-channel weak-rate closure

## Why this version exists

An isolated synthetic conformance fixture reproduced a substantive v0.9.19 false pass. The returned process history set both charged-lepton capture columns to zero,

- `e++n->p+nuebar = 0`, and
- `e-+p->n+nue = 0`,

while keeping the two neutrino-capture columns and setting neutron beta decay to `1/tau_n` at every temperature. Process sums, detailed-balance sanity, raw-evidence linkage, paired refinement, and the v0.9.19 provider firewall all passed. This is a software-contract counterexample, not a physical result and not an allegation about an external backend.

At `T_gamma=5 MeV`, the independent finite-electron-mass Born audit gives

| quantity | value (s^-1) |
|---|---:|
| positron capture on neutron | 1607.3057609847 |
| electron capture on proton | 1241.0766156987 |
| finite-temperature blocked beta decay | 0.0003231043942 |
| returned beta column in the counterexample | 0.0011371389584 |

The counterexample returned only about 50.002% of the complete five-channel Born `n->p` total and 49.998% of the complete five-channel Born `p->n` total at that node.

## New acceptance rule

v0.9.20 independently recomputes all five frozen canonical columns from the returned `f_nue`, `f_nuebar`, `q_grid`, `q_weights`, `p_per_q_MeV`, `T_gamma_MeV`, and `neutron_lifetime_s`.

The common normalization is

\[
I_0=\int_{m_e}^{\Delta_{np}} E_e\sqrt{E_e^2-m_e^2}(\Delta_{np}-E_e)^2\,dE_e,
\qquad A=(\tau_n I_0)^{-1}.
\]

Each non-negligible process column must be within 25% of its audit-only Born history. In addition, each direction total must be within 10% of the independently normalized sum of its Born columns. The tighter direction-total lane catches a common scaling that preserves process sums and relative channel shapes. The existing late gate remains: every beta-decay node with `T_gamma<=0.05 MeV` must satisfy `abs(lambda_beta*tau_n-1)<=0.005`.

The momentum grid must meaningfully refine both kinematic landmarks:

- antineutrino capture threshold `Delta_np+m_e = 1.80433131 MeV`;
- beta-decay endpoint `Delta_np-m_e = 0.78233341 MeV`.

## Interpretation limit

This is an execution firewall, not an independent corrected weak-rate calculation. Production radiative, recoil, weak-magnetism, finite-nucleon-mass, and plasma corrections remain authoritative if they lie inside the audit envelopes. The frozen five-column ontology does not separately export the inverse three-body process `p+e-+nuebar->n`; that remains an explicit scope limitation. Passing does not validate transport, BBN nuclear physics, or the DMDE hypothesis.

The machine-readable reproduction is `receipts/DMDE_v0920_WEAK5_FALSE_PASS_RECEIPT.json`.
