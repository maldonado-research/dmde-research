#!/usr/bin/env python3
"""Verify canonical public-round identities while retaining documented negatives."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(base, manifest, envelope=None):
    entries = json.loads((base / manifest).read_text())
    if envelope is not None:
        entries = entries[envelope]
    for name, expected in entries.items():
        relative = Path(name)
        target = (base / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(base.resolve()):
            raise RuntimeError(f'Unsafe manifest path: {name}')
        if digest(target) != expected:
            raise RuntimeError(f'Artifact identity mismatch: {base.name}/{name}')
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Create a new receipt; existing paths are refused')
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error('Refusing to overwrite an existing receipt')
    checks = {}
    for relative, manifest, envelope in [
        ('.', 'ARTIFACT_SHA256.json', None),
        ('source-audit', 'AUDIT_ARTIFACT_SHA256.json', None),
        ('coverage', 'ARTIFACT_SHA256.json', None),
        ('native-probe', 'artifact_sha256_complete.json', 'file_sha256'),
        ('native-probe/results-2026-10-01', 'artifact_sha256.json', None),
        ('native-probe/results-2026-10-01-corrected-rhs', 'artifact_sha256.json', None),
        ('native-probe/results-2026-10-01-final-rhs', 'artifact_sha256.json', None),
        ('review', 'ARTIFACT_SHA256.json', None),
    ]:
        checks[f'{relative}/{manifest}'] = verify(ROOT / relative, manifest, envelope)
    legacy = ROOT / 'native-probe/artifact_sha256.json'
    known = json.loads(legacy.read_text())['artifact_sha256.json']
    if known != hashlib.sha256(b'').hexdigest() or known == digest(legacy):
        raise RuntimeError('The documented legacy self-hash negative evidence has changed')
    receipt = {
        'status': 'PASS_CANONICAL_ARTIFACT_IDENTITIES_ONLY',
        'canonical_manifest_entries_verified': checks,
        'known_legacy_manifest_self_hash_failure_preserved': True,
        'scope': 'Recorded file identities, not scientific correctness, execution honesty or physical validation.',
    }
    rendered = json.dumps(receipt, indent=2) + '\n'
    if args.output is not None:
        with args.output.open('x') as handle:
            handle.write(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
