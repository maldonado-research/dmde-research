"""Check the unchanged public DMDE release without executing a cosmology run."""
from pathlib import Path
import csv
import hashlib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "provider"
RELEASE = ROOT / "releases/v0.9.20"
ARCHIVE = RELEASE / "DMDE_v0920_PROVIDER_DISPATCH_READY_SOURCE_FROZEN_WEAK5_GATED.zip"
ARCHIVE_SHA256 = "2daa4fa4c9d8654520ac8be0bd7a13197f447e85d4f10f36e7ba944c15d22b9b"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if sha256(ARCHIVE.read_bytes()) != ARCHIVE_SHA256:
        raise ValueError("Original provider ZIP SHA-256 mismatch")
    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None:
            raise ValueError("Provider ZIP CRC failure")
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        expected = set()
        for entry in entries:
            name = Path(entry.filename)
            # Read member bytes directly, never extract paths from an archive.
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("Unexpected archive path")
            # The original provider archive stores files directly at its root.
            target = PROVIDER / name
            if not target.is_file() or target.read_bytes() != archive.read(entry):
                raise ValueError(f"Extracted provider file differs: {name}")
            expected.add(name.as_posix())
        actual = {p.relative_to(PROVIDER).as_posix() for p in PROVIDER.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        if actual != expected:
            raise ValueError("Provider file membership differs from public archive")
    print(f"PASS: original ZIP and {len(expected)} provider files")
    with (PROVIDER / "manifest/DMDE_v0920_PROVIDER_FILE_MANIFEST_SHA256.csv").open(newline="") as handle:
        provider_rows = list(csv.DictReader(handle))
    for row in provider_rows:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unexpected provider manifest path")
        data = (PROVIDER / relative).read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise ValueError(f"Provider manifest mismatch: {relative}")
    print(f"PASS: {len(provider_rows)} provider manifest entries")
    # Published artifact hashes are stored in the release CSV. Its own hash is
    # pinned here because a manifest cannot authenticate itself.
    manifest = RELEASE / "DMDE_v0920_PUBLIC_ARTIFACT_SHA256.csv"
    if sha256(manifest.read_bytes()) != "b8bfd85b5bf428be8ae32fcf5cd1e3b7260040ed2ce65bfeee94057704038e83":
        raise ValueError("Published artifact manifest mismatch")
    with manifest.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        path = RELEASE / row["filename"]
        if sha256(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"Published artifact hash mismatch: {path.name}")
    print(f"PASS: {len(rows)} published artifact entries and manifest identity")


if __name__ == "__main__":
    main()
