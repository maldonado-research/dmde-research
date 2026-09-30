# DMDE Research

**Dark matter–dark energy working hypothesis · v0.9.20 methods/software checkpoint**

Research by **Ricardo Maldonado**. This repository makes the published DMDE source specification and validation tools easier to inspect, cite, and reproduce.

[![Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22399940.svg)](https://doi.org/10.5281/zenodo.22399940)

## In More Basic Terms

How could we test an idea about the unseen universe? One route is to calculate what its proposed particles would change in the universe’s first elements.

DMDE’s current test holds two particle-injection scenarios fixed. It asks a future calculation to follow their neutrinos, the reactions that turn neutrons and protons into one another, and the formation of helium and deuterium. Version 0.9.20 strengthens the checks along that chain so a calculation is less likely to pass while omitting an important contribution or ignoring its input.

It also works out how closely the two sources are matched and how precise a future comparison would need to be. This is progress in designing and checking a test. The release does not yet show that DMDE explains dark matter, dark energy, or a unified theory.

## What the release contains

- Two byte-frozen, blinded spectral-source payloads with shared timing and neutrino shapes and different amplitudes.
- Public Python validators, schemas, input templates, and provider execution contracts.
- A five-process weak-rate audit, including charged-lepton capture and finite-temperature neutron-decay blocking.
- Source-shape, source-time, transport-stepper, nuclear-input-consumption, and meaningful-refinement requirements.
- A source-only calculation of the pair’s differential-response geometry and conditional precision requirements.
- Saved public receipts and the original five-file Zenodo release set.

The [provider directory](provider/) preserves all 74 files from the public provider ZIP byte for byte. The [release directory](releases/v0.9.20/) preserves the five published artifacts, including the original archive, plain-language README, release-note PDF, verification JSON, and SHA-256 manifest.

## Scientific status

This is a working hypothesis and a methods/software release. It is not peer reviewed. **No validated production predictions for the two injected scenarios’ helium abundance, deuterium abundance, or effective neutrino number are supplied.** Production momentum-dependent transport, corrected weak rates, an instrumented BBN calculation, and independent backend replication remain pending.

Software and file-integrity checks do not establish physical validity or prove honest execution. The five exported weak histories do not separately represent the inverse three-body process, and their Born-reference audit is not a complete precision weak-rate treatment. The exact source-pair identities do not determine the sign or magnitude of a final abundance response. The approximately twenty-parts-per-million precision example is a conditional design target, not achieved accuracy or a detection.

The wider physical model, including its complete microscopic origin and connection to dark energy, needs its own derivations and tests. This repository does not establish a theory of everything.

## Start reading

1. [Public explanation in more basic terms](releases/v0.9.20/DMDE_v0920_README_IN_MORE_BASIC_TERMS.md).
2. [Provider dispatch overview](provider/README_PROVIDER_DISPATCH.md).
3. [Validation scope and limits](provider/docs/DMDE_v0920_VALIDATION_SCOPE_AND_LIMITS.md).
4. [Five-process audit and false-pass repair](provider/docs/DMDE_v0920_WEAK5_CLOSURE_AND_FALSE_PASS.md).
5. [Frozen-pair differential response](provider/docs/DMDE_v0920_FROZEN_PAIR_DIFFERENTIAL_RESPONSE_RESULT.md).
6. [Reproduce the public source checks](REPRODUCING.md).

## Reproduce the public source checks

Use Python 3.10+ and NumPy 2.0+. The example lock is NumPy 2.3.5, matching the documented verification environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/check_public_release.py
mkdir -p generated
python3 provider/code/dmde_v0920_validate_blind_payloads_deep.py --base provider \
  --out-csv generated/deep_payload_validation.csv \
  --out-json generated/deep_payload_validation.json
python3 provider/code/dmde_v0920_pair_geometry.py --provider-root provider \
  --json-out generated/pair_geometry.json --csv-out generated/precision_design.csv
```

These commands check public artifacts and source mathematics. They do not run neutrino transport or BBN. The private 67-test analyst suite is not included; see the reproduction note about legacy wording in two preserved documents.

## Citation, license, and provenance

The archival research reference is:

Ricardo Maldonado, *DMDE Triplepoint + CosmoGate: Five-Channel Weak-Rate Closure and Frozen-Pair Differential-Response Design (v0.9.20)*, Zenodo, published 5 September 2026. [DOI: 10.5281/zenodo.22399940](https://doi.org/10.5281/zenodo.22399940).

- Source/software date: 17 August 2026.
- GitHub packaging prepared: 30 September 2026; this does not introduce new physical results or a new research version.
- [All-version DOI](https://doi.org/10.5281/zenodo.18135951).
- [Earlier public checkpoint](https://zenodo.org/records/20187862).
- [Citation metadata](CITATION.cff).
- [License and attribution](LICENSE.md): CC BY 4.0 for this published release, unless a file states otherwise. External backends are referenced; their source code is not bundled or relicensed here.

Private scoring, unblinding material, analyst fixtures, and unpublished editorial article drafts are not included. Repository-level explanatory and packaging files were prepared with AI assistance from the public research record; they are not an independent scientific endorsement.

Questions, reproducibility reports, and corrections are welcome. Please identify the file or claim, the version used, and enough detail to reproduce an issue.
