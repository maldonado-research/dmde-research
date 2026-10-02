# DMDE numerical controls — 1 October 2026

This dated research supplement adds reproducible numerical controls to the preserved v0.9.20 release. It supplies no injected-scenario predictions, observational detection, dark-energy derivation, or independent physical confirmation. It is not peer reviewed. The research program is Ricardo Maldonado's; these calculations and records were prepared with AI assistance.

## In More Basic Terms

We checked two prerequisites for a trustworthy future test. First, an established early-universe program can calculate its ordinary Standard Model control here. Second, a separate reaction calculation shows exactly what the current five-process reference leaves out. Neither calculation says the proposed particles explain dark matter or dark energy.

## Results and reproduction

- [Six-process equilibrium audit](2026-10-01-equilibrium-audit/README.md): a static, lifetime-normalized Born calculation, with a separately implemented numerical review. The omitted inverse neutron-decay reaction is required for exact equilibrium reciprocity. At a common temperature of 0.25 MeV, the complete proton-to-neutron coefficient is approximately 22.36% above the five-process coefficient. A large relative late-time discrepancy does not establish a large abundance effect. Equilibrium ratios also fail to expose identically clipped integration tails.
- [PRIMAT Standard Model controls](2026-10-01-sm-control/README.md): executions of the official Python backend at recorded historical and current commits, using upstream shipped caches. These execute the nuclear network for a Standard Model control; they do not recompute momentum-dependent neutrino transport or certify the cached weak rates. The small-network result is approximately `Yp=0.24699895`, `D/H=2.4358600e-5`, `Neff=3.0439773`. The historical audit's bare scalar receipt is not exactly reproduced; its full settings are unavailable, and the difference is retained.
- [Claim ledger](CLAIM_LEDGER.md) separates mathematical identities, numerical checks, assumptions, and missing physical evidence.
- [Next tests](NEXT_TESTS.md) defines the next integration work and the results it must not be mistaken for.
- [Separate computational review](2026-10-01-independent-review/AUDIT.md) checks the equations with adaptive integration in a different variable and reviews the control receipts. This is not external peer review.

The frozen provider files and release artifacts remain unchanged. The supplement does not silently revise the five-column return contract or create a new Zenodo release. Use the individual reproduction guides and recorded environment/source hashes; do not replace the historical receipts with newly generated output.

The controls have distinct purposes and settings: the Born diagnostic uses a neutron lifetime of 879.4 s, while PRIMAT uses its default 878.4 s. They are not a combined calibration or matched abundance comparison.

Current paper retrieval and GitHub API operations were blocked by this cloud instance's restricted network policy. This supplement is not a survey of developments through October 2026. Existing Git access permitted source inspection. Live website deployment, pull-request creation, and Zenodo publication require their respective supported access and are separate from a successful calculation.
