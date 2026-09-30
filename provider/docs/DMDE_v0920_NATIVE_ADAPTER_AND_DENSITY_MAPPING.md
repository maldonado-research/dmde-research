# Native adapter and start-density mapping

For each blind source card, map the frozen fields to the public batch interface as follows:

```text
mass          = mass_MeV
lifetime      = tau_s
numberDensity = Y0 * (2*pi^2/45) * g_starS(Tstart) * Tstart^3
muonBranching = 2*B_mumu
pionBranching = 0
lifetimeFactor = 18
decayFile     = None  # prompt stopped-muon source assumption
direct-neutrino columns = OMIT
```

The reference conversion uses `initialX=0.1`,

\[
T_{\rm start}=1.00003\,m_e/0.1=5.11014229967\ {\rm MeV},
\]

and $g_{*S}=10.75$. It gives the reference start densities already listed in `DMDE_v0920_NUDEC_NATIVE_MAPPING.csv`. These are interface-reference values, not permission to substitute a different entropy convention silently. Production evidence must state the entropy density, QED equation-of-state treatment, electron-mass convention, and exact start-temperature mapping used.

The native muon field is the average number of primary muons per LLP decay. The frozen source field is a $\mu^+\mu^-$ pair probability, hence $N_\mu=2B_{\mu\mu}$. Supplying three direct-neutrino columns filled with zeros is not equivalent to omitting those fields in the public interface and can alter momentum-domain handling; omit them.

The source payload uses $m_\mu=105.6583755$ MeV. Do not replace it with the backend's rounded internal default without explicitly patching or parameterizing the source implementation and recording that code artifact.
