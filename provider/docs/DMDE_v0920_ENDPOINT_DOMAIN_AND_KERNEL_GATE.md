# Endpoint-domain and weak-kernel quadrature gate

The upstream public solver defines physical momentum as

\[
p(q,x)=q\,m_e/x.
\]

For a stopped-muon endpoint $p_\star=m_\mu/2$, endpoint-complete support at the final injection point therefore requires

\[
q_{\max}\ge \frac{x_{\rm stop}}{m_e}\frac{m_\mu}{2}.
\]

The public `Core.py` expression uses $x_{\rm stop}m_\mu/2$, while `System_Nudecoupling.py` reconstructs $p=q m_e/x$. For the frozen source mass $m_\mu=105.6583755$ MeV and $x_{\rm stop}=16.993868549367075$, the two values are approximately 897.7723 and 1756.8967. v0.9.20 does not depend on a variable-name interpretation: it directly checks that the returned physical domain satisfies

\[
q_{\max}p_{\rm per\,q}(18\tau)\ge m_\mu/2.
\]

Increasing the bin count at a clipped fixed endpoint is not an acceptable domain refinement.

The restored Michel ladder is

\[
M_{e,k}=\frac{12}{(k+3)(k+4)},\qquad
M_{\mu,k}=\frac{2(k+6)}{(k+3)(k+4)},\qquad k=0,\ldots,5,
\]

with physical moments $(m_\mu/2)^kM_{a,k}$. Each ideal-grid representability error and each corresponding actual source-RHS moment error must be at most $5\times10^{-3}$. The bridge validator also checks two zero-blocking Born kinematic capture proxies. The antineutrino sentinel now enforces the physical static threshold $E_\nu-\Delta_{np}\ge m_e$. These are grid sentinels only; they do not replace production recoil, radiative, finite-mass, blocking, or plasma corrections.

Upstream source inspected at commit `0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62` (2025-08-21):

- [Core.py](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Core.py)
- [System_Nudecoupling.py](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/System_Nudecoupling.py)
- [Distributions.py](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Distributions.py)
- [Constants.py](https://github.com/baugid/Nudec_LLP_Solver/blob/0a4b7a0e174c2320cc7e9549a51f22ccb9e40d62/Constants.py)
