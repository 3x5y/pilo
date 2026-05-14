from dataclasses import dataclass
from pathlib import Path

from . import checksum
from . import manifest_model


@dataclass(frozen=True)
class ContinuityMapping:
    src_subset: str
    dst_subset: str
    src: Path
    dst: Path


@dataclass(frozen=True)
class ContinuityTransfer:
    src_subset: str
    dst_subset: str
    src: Path
    dst: Path
    checksum: str
    provenance: manifest_model.ChecksumProvenance


def build_transfers(mappings, verified):

    verified = manifest_model.as_checksum_index(verified)
    transfers = []

    for m in mappings:
        item = verified.require(m.src)
        transfers.append(
            ContinuityTransfer(
                src_subset=m.src_subset,
                dst_subset=m.dst_subset,
                src=m.src,
                dst=m.dst,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return transfers


def build_mutations(transfers):

    muts = []
    for transfer in transfers:
        muts.append(
            manifest_model
            .ManifestRemoveEntry(
                subset=transfer.src_subset,
                path=transfer.src,
            )
        )
        muts.append(
            manifest_model
            .ManifestAddEntry(
                subset=transfer.dst_subset,
                entry=manifest_model
                    .ManifestEntry(
                        checksum=transfer.checksum,
                        path=transfer.dst,
                    )
            )
        )
    return muts


def acquire_verified_checksums(paths, entries):

    index = manifest_model.as_manifest_index(entries)
    verified = []

    for rel_path, real_path in paths:
        existing = index.require(rel_path)
        verified_item = checksum.verify_checksum(real_path, existing.checksum)
        verified.append(
            manifest_model.ProvenancedChecksum(
                path=rel_path,
                checksum=verified_item.checksum,
                provenance=verified_item.provenance,
            )
        )
    return manifest_model.ChecksumIndex(verified)


def acquire_generated_checksums(paths):

    generated = []
    for rel_path, real_path in paths:
        item = checksum.generate_checksum(real_path)
        generated.append(
            manifest_model.ProvenancedChecksum(
                path=rel_path,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return manifest_model.ChecksumIndex(generated)
