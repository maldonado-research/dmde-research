# DMDE v0.9.20 weak-rate and BBN-consumption causal closure

This staged contract closes two execution-observability gaps without changing a frozen DMDE source card, physical parameter, branch, or private scoring rule.

## Weak-rate closure

The bridge must use these exact grouped process columns and order:

1. `nu_e+n->p+e-`
2. `e++n->p+nuebar`
3. `n->p+e-+nuebar`
4. `nuebar+p->n+e+`
5. `e-+p->n+nue`

The validator checks each direction's process sum against its total. It then independently evaluates all five finite-electron-mass Born processes from the returned `f_nue`, `f_nuebar`, momentum nodes and weights, physical-momentum scale, and photon temperature.

Let

\[
I_0=\int_{m_e}^{\Delta_{np}}
E_e\sqrt{E_e^2-m_e^2}(\Delta_{np}-E_e)^2\,dE_e,
\qquad A=(\tau_n I_0)^{-1}.
\]

With `p` the massless (anti)neutrino energy, the five audit integrands, excluding the common `A dp`, are

\[
\begin{aligned}
\nu_e+n &: p^2 f_{\nu_e} E_+p_+[1-f_e(E_+)],\\
e^++n &: p^2 E_-p_-f_{e^+}(E_-)[1-f_{\bar\nu_e}],\\
n\;\text{beta decay} &: p^2 E_dp_d[1-f_e(E_d)][1-f_{\bar\nu_e}],\\
\bar\nu_e+p &: p^2 f_{\bar\nu_e}E_-p_-[1-f_{e^+}(E_-)],\\
e^-+p &: p^2 E_+p_+f_e(E_+)[1-f_{\nu_e}],
\end{aligned}
\]

where

\[
E_+=p+\Delta_{np},\qquad
E_-=p-\Delta_{np}\ge m_e,\qquad
E_d=\Delta_{np}-p\ge m_e.
\]

For each charged lepton, `p_e=sqrt(E_e^2-m_e^2)`.

The electron and positron sentinel distributions are zero-chemical-potential Fermi-Dirac distributions at `T_gamma_MeV`; outgoing neutrinos use the returned spectra for Pauli blocking. Every canonical process column must remain within 25% of its Born lane wherever that lane exceeds `max(1e-18 s^-1, 1e-10*peak)`. Each direction total must also remain within 10% of the independently normalized sum of its Born lanes. The deliberately conservative process band permits backend corrections; the tighter total lane rejects a common rate rescaling.

At every node with `T_gamma_MeV<=0.05`, the canonical free-neutron-decay column must obey

\[
|\lambda_{n\rightarrow p}^{\rm decay}\tau_n-1|\le 0.005.
\]

Momentum-resolved production rate integrands are optional in this stage. When declared or supplied, the four integrand/non-grid arrays are an all-or-none contract, and every process column must equal its weighted momentum integral plus its non-grid residual.

The physical momentum refinement certificate must reduce cell widths around both `Delta_np+m_e` and the beta endpoint `Delta_np-m_e`. The frozen five-column ontology does not separately export the inverse three-body `p+e-+nuebar->n` process; this is an explicit scope limit.

## BBN-consumption canary

The baseline replay input and output must be byte-identical to the declared production BBN input and output. The code, configuration, every input, every output, and the summary CSV are linked by exact lowercase SHA-256 values.

Four shadow inputs are derived from the baseline. Only the named weak rate is multiplied, only at rows satisfying

\[
0.5\ {\rm MeV}\le T_\gamma\le1.2\ {\rm MeV},
\]

and every other field and row remains numerically identical:

- `lambda_n_to_p_s_inv` by 1.01 and 1.005;
- `lambda_p_to_n_s_inv` by 1.01 and 1.005.

Both neutron-to-proton perturbations must produce negative `DeltaYp`; both proton-to-neutron perturbations must produce positive `DeltaYp`. Every response must exceed the declared deterministic noise floor. For each direction, the absolute 1% response divided by the absolute 0.5% response must lie in `[1.5,2.5]`.

This is a consumption and sensitivity canary. It does not establish that the nuclear network, its rates, or the resulting abundance prediction are physically correct.

## Commands

```bash
python code/dmde_v0920_validate_weak_rate_closure.py BRIDGE.npz WEAK_METADATA.json
python code/dmde_v0920_validate_bbn_canary.py DMDE_v0920_BBN_CANARY.json
python -m unittest discover -s tests -v
```
