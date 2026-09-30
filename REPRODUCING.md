# Reproducing the Public DMDE Checks

## What can be reproduced from this repository

The repository supplies frozen source files and public checking code. It can reproduce source validation, pair geometry, and integrity checks. It does not supply a complete production neutrino-transport/BBN solver, validated injected outputs, or the private analyst test suite.

## Environment

Python 3.10+ and NumPy 2.0+ are the documented minimum. The source release reports Python 3.12.13 / NumPy 2.3.5. The 5 September public verification reports Python 3.12.14 / NumPy 2.3.5. This repository pins NumPy 2.3.5 for a reproducible example; record the actual Python and platform versions used.

The source checks require no network after the dependency is installed. Run the commands from the repository root. Generated results are kept outside provider/ so the published packet remains unchanged.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/check_public_release.py
mkdir -p generated
python3 provider/code/dmde_v0920_validate_blind_payloads_deep.py --base provider \
  --out-csv generated/deep_payload_validation.csv \
  --out-json generated/deep_payload_validation.json
python3 provider/code/dmde_v0920_pair_geometry.py --provider-root provider \
  --json-out generated/pair_geometry.json --csv-out generated/precision_design.csv
```

The integrity script checks the original ZIP hash and its CRC, exact equality between its extracted members and provider/, the 73 internal manifest entries, and the five published artifact hashes. Deep validation should accept both frozen payloads. Pair geometry should reproduce the declared source contrasts and precision design within normal numerical representation limits.

## Interpreting a pass

These checks concern file identity, source formulas, source integrals, and conditional mathematical relationships. They are not an experimental test of a dark particle, a prediction of primordial abundances, or independent backend replication. Some tiny floating-point residuals in newly generated receipts can differ across supported environments; acceptance under stated tolerances is distinct from byte identity of a historical receipt.

## Historical wording to read carefully

The original provider files are preserved rather than silently edited:

- provider/docs/DMDE_v0920_CAUSAL_CLOSURE_CONTRACT.md mentions unittest discovery, but this public packet does not contain the private tests/ tree.
- provider/docs/DMDE_v0920_FROZEN_PAIR_DIFFERENTIAL_RESPONSE_RESULT.md suggests that the source calculation commands also run six unit tests. The commands compute source geometry; they do not invoke those tests.

The saved 67-test result belongs to the earlier local private analyst suite. This repository does not claim to reproduce all 67 tests.

## A future production return

Follow provider/docs/DMDE_v0920_PROVIDER_RUNBOOK.md, the spectral-to-BBN bridge contract, raw-evidence contract, and validation commands. Placeholder templates are instructions, not results. Both frozen scenarios require momentum-resolved transport, the declared weak-rate linkage, nuclear consumption evidence, and meaningful refinement. Validate complete returns before interpreting their output contrast.

Independent physical review and implementation remain necessary even after a return passes the public checks.
