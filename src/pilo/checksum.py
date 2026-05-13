from pathlib import Path

from . import error
from . import fs
from . import manifest_model


def generate_checksum(path: Path):
    checksum = fs.sha256_file(path)
    return (
        manifest_model.ProvenancedChecksum(
            path=path,
            checksum=checksum,
            provenance=(
                manifest_model
                .ChecksumProvenance
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
        manifest_model.ProvenancedChecksum(
            path=path,
            checksum=expected_checksum,
            provenance=(
                manifest_model
                .ChecksumProvenance
                .VERIFIED
            ),
        )
    )


def reuse_manifest_checksum(entry):
    return (
        manifest_model.ProvenancedChecksum(
            path=entry.path,
            checksum=entry.checksum,
            provenance=(
                manifest_model
                .ChecksumProvenance
                .MANIFEST
            ),
        )
    )
