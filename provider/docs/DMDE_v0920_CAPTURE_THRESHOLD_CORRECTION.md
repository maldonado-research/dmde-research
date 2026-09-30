# Antineutrino capture-sentinel threshold correction

The v0.9.17 Born capture sentinel for `anti-nu_e + p -> n + e+` tested only

\[
(E_\nu-\Delta_{np})^2-m_e^2\ge0.
\]

That condition also admits the unphysical negative-energy branch `E_nu-Delta_np <= -m_e`, producing a tiny negative contribution below threshold.

v0.9.20 requires the physical static-nucleon condition

\[
E_\nu-\Delta_{np}\ge m_e,
\]

so the sentinel opens at

\[
E_{\rm th}^{\rm static}=\Delta_{np}+m_e=1.80433131\ {m MeV}.
\]

The removed contribution is approximately `4.44e-9` of the physical Michel-averaged proxy, far below the `5e-3` sentinel ceiling. This correction changes no frozen source, acceptance conclusion, or physical result. It is included because v0.9.20 already revises the validator for the substantive source-operator gate.

Production weak rates must use the threshold and recoil treatment belonging to their documented implementation; this static Born expression remains only a grid sentinel.
