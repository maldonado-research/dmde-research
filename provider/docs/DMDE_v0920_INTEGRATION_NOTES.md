# Integration notes for the v0.9.20 causal validators

These validators are integrated into the v0.9.20 provider-return and raw-evidence
firewalls. This note records the binding order and required archive roles.

## Provider-return validation order

For every coarse and fine bridge returned for both blind cards:

1. Run the frozen-source and base bridge validator.
2. Run `validate_weak_rate_closure(bridge_npz, weak_rate_metadata_json)`.
3. Run raw-evidence ZIP validation and cross-link the weak metadata to the raw archive.
4. Extract the already security-validated raw archive into an isolated temporary directory, then run `validate_bbn_canary(extracted_root / "DMDE_v0920_BBN_CANARY.json")`.
5. Only after all four run-level causal validations pass, run paired coarse/fine convergence and the unchanged private scorer.

Any weak-rate or BBN-canary failure must block scoring. Self-reported CSV pass fields cannot override these results.

The weak-rate metadata and BBN canary contract are fixed, manifest-covered raw
archive members. Their hashes are bound through the raw contract rather than
duplicated as provider-return CSV columns.

## New raw-evidence roles and paths

Add these mandatory roles to each coarse/fine raw archive:

- `weak_rate_closure_metadata`: `evidence/weak_rate_closure_metadata.json`
- `bbn_code_artifact`: `bbn/code_artifact.bin`
- `bbn_config`: `bbn/config.json`
- `bbn_canary_contract`: `DMDE_v0920_BBN_CANARY.json`
- `bbn_canary_baseline_input`: `bbn_canary/replays/baseline_rate_input.csv`
- `bbn_canary_baseline_output`: `bbn_canary/replays/baseline_output.json`
- `bbn_canary_summary`: `bbn_canary/replays/canary_summary.csv`
- four `bbn_canary_rate_input_*` roles under `bbn_canary/replays/`
- four `bbn_canary_output_*` roles under `bbn_canary/replays/`

The canary contract should sit at the raw archive root so it can safely reference existing production roles without `..` paths:

- `production.rate_input.path = "bbn/rate_input.csv"`
- `production.output.path = "evidence/final_outputs.json"`
- `code.path = "bbn/code_artifact.bin"`
- `config.path = "bbn/config.json"`

All canary replay paths remain below `bbn_canary/replays/`.

## Mandatory cross-links in the raw validator

The standalone weak validator verifies the syntax of its declared code/config digests. The integrated raw validator must additionally require:

- weak metadata `bridge_history_sha256` equals the external bridge and internal `bridge/history.npz` hash;
- weak metadata bytes equal `evidence/weak_rate_closure_metadata.json` bytes;
- `weak_rate_code_sha256` equals the raw backend weak-rate code artifact hash;
- `weak_rate_config_sha256` equals the exact raw weak-rate/BBN configuration hash;
- `weak_rate_production_callable` equals the controlled solver-configuration field;
- the exact canonical process labels agree across weak metadata, bridge metadata, and process-array column order;
- the BBN canary production input/output references equal the raw `bbn/rate_input.csv` and `evidence/final_outputs.json` bytes;
- the BBN code/config hashes agree with their required raw roles;
- every canary file is covered exactly once by the raw manifest.

The controlled coarse/fine configuration fingerprint should cover the weak callable, canonical process map, Born-lane convention, BBN code/config, canary window, perturbation fractions, and deterministic noise-floor definition. Only the grid/run-role differences already authorized by the refinement contract may differ.

## Extraction safety

Do not call the filesystem-based BBN validator on an uninspected ZIP. First apply the existing raw archive member-count, size, compression-ratio, CRC, path, symlink, duplicate-name, and manifest-coverage checks. Materialize only validated canonical members into a newly created temporary directory, then call the validator. Alternatively, port the same logic to a byte-backed archive adapter.

## Known limits

- The Born lane independently checks all five exported process groups with a 25% per-process band and a 10% direction-total band. These audit envelopes deliberately permit modest backend-specific physical corrections; they do not validate those corrections. The frozen ontology does not separately export `p+e-+nuebar->n`.
- The 25% beta-process envelope checks finite-temperature blocking only as a broad Born sentinel; it is not a precision validation of corrected beta-decay physics. The separate late lifetime gate fixes the vacuum normalization.
- Momentum-integrand closure proves arithmetic linkage, not that an honest production callable generated the arrays.
- The BBN canary proves byte identity, input derivation, consumption sensitivity, and expected response direction. It does not validate the nuclear network, reaction-rate library, or abundance physics.
- Hashes establish byte linkage, not truthful execution. Code review and independent replay remain required.
- These two validators do not close source-RHS-to-transport-state evolution. That witness remains a separate v0.9.20 module/gate.
