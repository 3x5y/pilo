from pathlib import Path

from .. import error
from .. import fs
from . import manifest


def generate_checksum(path: Path):
    checksum = fs.sha256_file(path)
    return (
        manifest.ProvenancedChecksum(
            path=path,
            checksum=checksum,
            provenance=(
                manifest.ChecksumProvenance
                .GENERATED
            ),
        )
    )


def verify_checksum(path: Path, expected_checksum: str):
    actual = fs.sha256_file(path)
    if actual != expected_checksum:
        error.fatal(
            f"checksum verification failed: "
            f"{path}"
        )
    return (
        manifest.ProvenancedChecksum(
            path=path,
            checksum=expected_checksum,
            provenance=(
                manifest.ChecksumProvenance
                .VERIFIED
            ),
        )
    )


def reuse_manifest_checksum(entry):
    return (
        manifest.ProvenancedChecksum(
            path=entry.path,
            checksum=entry.checksum,
            provenance=(
                manifest.ChecksumProvenance
                .MANIFEST
            ),
        )
    )
