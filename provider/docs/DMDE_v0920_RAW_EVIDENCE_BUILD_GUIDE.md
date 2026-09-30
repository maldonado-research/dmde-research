# Raw-evidence build guide

Create one canonical ZIP per run. Use only stored or deflate compression. Every non-manifest member must be a regular file with a unique, case-stable POSIX path and one unique role. Do not include directories, symlinks, devices, encryption, archive/member comments, ZIP extra fields, absolute or dot-segment paths, duplicate Unicode-normalized names, or bytes after the end-of-central-directory record.

Required fixed paths and roles are defined in `schemas/DMDE_v0920_RAW_EVIDENCE_SCHEMA.json`. The backend code role must contain the exact source snapshot, executable, or patch artifact whose SHA-256 appears in the backend identity and contract. `bbn/rate_input.csv` must contain the exact declared time, photon-temperature, Hubble, and total weak-rate arrays supplied to the BBN network. `bbn/abundance_history.csv` must end at the returned $Y_p$ and D/H.

The solver configuration and bridge metadata must identically record the
source-RHS stage/units/callable/adapter, canonical state normalization,
production stepper and source-only toggle, weak-rate callable/process map/Born
lane, and BBN canary command. The operator receipt hashes all eight selected
initial states. An independently reconstructed source, weak-rate, or BBN
sidecar does not satisfy the declared contract.

Include `evidence/weak_rate_closure_metadata.json` and the exact canonical
five-process column order. At the archive root include
`DMDE_v0920_BBN_CANARY.json`; its fixed references point to the production
input/output, BBN code/config, byte-identical baseline replay, four derived
inputs and outputs, and canonical summary below `bbn_canary/replays/`.

Serialize CSV floats with sufficient precision to round-trip to the bridge's binary64 value—Python `repr(float(value))` or 17 significant decimal digits is suitable. Headers and column order are exact. Use UTF-8 without a byte-order mark and LF line endings.

Create `DMDE_RAW_EVIDENCE_MANIFEST.csv` last. Its header is exactly `path,role,bytes,sha256`; rows cover every non-manifest member once, are sorted by path, contain canonical decimal byte counts, and lowercase SHA-256 values. The manifest does not list itself.

Fixed container ceilings are:

- archive: 1.1 GiB;
- members: 256;
- one member: 512 MiB;
- total uncompressed: 2 GiB;
- total compressed: 1 GiB;
- member expansion ratio: 250;
- manifest: 4 MiB;
- captured text evidence: 64 MiB per member.

Build coarse and fine archives from the same backend code and environment and identical non-grid solver/BBN configuration. The validator derives a controlled-configuration fingerprint; only run role, momentum-bin count, and momentum-grid description may differ. Use one identical `refinement_settings` string in both archives to describe the paired comparison as a whole.

The Standard Model control object is a provider-reported, converged, backend-matched summary. Preserve the underlying control run for analyst inspection even though it is not a fifth required archive in this contract.
