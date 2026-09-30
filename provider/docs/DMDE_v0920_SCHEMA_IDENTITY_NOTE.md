# Frozen payload-schema identity note

The source-card contract historically identifies the separable return payload as `DMDE-SPECTRAL-SEPARABLE-PAYLOAD-v0.9.8`. The unchanged documentation file `DMDE_v099_PAYLOAD_SCHEMA.json` internally carries the later label `DMDE-SPECTRAL-TENSOR-PAYLOAD-v0.9.9`.

v0.9.20 does not silently retag either frozen object. For return identity and firewall matching, use `DMDE-SPECTRAL-SEPARABLE-PAYLOAD-v0.9.8`. Preserve the documentation file byte-for-byte; its SHA-256 is locked in `DMDE_v0920_expected_source_identities.csv` together with its internal label.

The two NPZ payloads do not contain an embedded schema-version array. The historical `V099` filename segment is therefore not an authoritative schema declaration; the frozen source-card contract and its locked byte lineage govern.

This note resolves naming, not physics. The two NPZ payload hashes remain unchanged.
