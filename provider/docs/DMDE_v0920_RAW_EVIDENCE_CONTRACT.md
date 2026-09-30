# Raw-evidence ZIP contract v0.9.20

Each coarse and fine run must have its own valid ZIP archive. Renaming a text file or README-only ZIP is not sufficient.

Required roles are listed in `schemas/DMDE_v0920_RAW_EVIDENCE_SCHEMA.json`.
The archive includes the frozen-source identity; exact bridge pair; hashed
transport/weak and BBN code/configuration; backend/environment identity;
invocation and logs; operator-probe receipt; weak-rate closure metadata; exact
five-process rate evidence; production BBN input/output and abundance history;
a byte-identical baseline replay; four canonical canary inputs and outputs;
the canary summary/contract; final outputs; and a complete SHA-256 manifest.
The source identity records the frozen payload hash; it does not pretend to
contain the payload bytes.

The validator verifies ZIP CRC, rejects encryption, unsafe paths,
duplicate/case-colliding names and symbolic links, applies bounded-expansion
ceilings, and hashes every member. It then binds operator state hashes to the
external bridge, recomputes the Born/lifetime weak-rate sentinels, proves the
baseline BBN replay is byte-identical, derives each rate perturbation, and
checks the signed, above-noise, near-linear `DeltaYp` responses.

For production, structured evidence must not contain synthetic/mock/fixture/test-only markers. The synthetic switch exists only in the private analyst packet for bundled software tests and is rejected by default.

This proves declared byte linkage and the specified causal canaries. It does
not prove that mutually consistent evidence was honestly produced, validate
backend-specific corrections or nuclear physics, or replace code review,
independent replay, and cross-backend replication.
