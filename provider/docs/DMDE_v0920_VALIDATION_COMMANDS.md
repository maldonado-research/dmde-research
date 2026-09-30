# Validation commands

Run from the extracted provider-packet root with Python 3.10+ and NumPy 2.0+.

Validate the frozen source payloads:

```bash
python3 code/dmde_v0920_validate_blind_payloads_deep.py --base . \
  --out-csv receipts/deep_payload_validation.csv \
  --out-json receipts/deep_payload_validation.json
```

Validate one returned bridge independently; the expected blind ID is mandatory:

```bash
python3 code/dmde_v0920_validate_bridge_bundle.py \
  returned/bridges/CARD_fine_bridge.npz \
  returned/bridges/CARD_fine_bridge.json \
  --base . --expected-blind-id DMDE-SPEC-V099-4Q7N \
  --out-json receipts/CARD_fine_bridge_validation.json
```

Validate one raw-evidence ZIP. This also runs the internal weak-rate closure
and BBN-consumption canary after the ZIP passes container/path/hash preflight:

```bash
python3 code/dmde_v0920_validate_raw_evidence.py \
  returned/raw/CARD_fine_raw_evidence.zip --base .
```

The weak-rate and BBN validators can also be run directly on an already safely
extracted archive:

```bash
python3 code/dmde_v0920_validate_weak_rate_closure.py \
  bridge/history.npz evidence/weak_rate_closure_metadata.json
python3 code/dmde_v0920_validate_bbn_canary.py DMDE_v0920_BBN_CANARY.json
```

Validate the complete two-card return. Unsuffixed CSV fields and paths are the fine runs:

```bash
python3 code/dmde_v0920_validate_provider_return.py returned/provider_return.csv \
  --base . --bridge-dir returned/bridges --raw-bundle-dir returned/raw \
  --out-csv receipts/provider_return_validation.csv \
  --out-json receipts/provider_return_validation.json
```

Success prints the corresponding `PASS` status and exits zero. Any missing
identity, archive, role, hash, source, state, stepper response, weak-rate
closure, BBN canary, configuration, refinement, or physical-range gate exits
nonzero. The provider commands expose no synthetic/conformance waiver.
