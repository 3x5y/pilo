from dataclasses import dataclass
from pathlib import Path

from ..content import checksum
from ..front import manifest


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
    provenance: manifest.ChecksumProvenance


@dataclass(frozen=True)
class ContinuityRemoval:
    subset: str
    path: Path


def build_transfer_mutations(mappings, verified):
    transfers = build_transfers(mappings, verified)
    return build_mutations(transfers)


def build_removal_mutations(removals):
    muts = []
    for removal in removals:
        muts.append(
            manifest.build_removal(
                removal.subset,
                removal.path,
            )
        )
    return muts


def build_transfers(mappings, verified):

    verified = manifest.as_checksum_index(verified)
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
            manifest.build_removal(
                transfer.src_subset,
                transfer.src,
            )
        )
        muts.append(
            manifest.build_addition(
                transfer.dst_subset,
                transfer.dst,
                transfer.checksum,
            )
        )
    return muts


def acquire_verified_checksums(paths, entries):

    index = manifest.as_manifest_index(entries)
    verified = []

    for rel_path, real_path in paths:
        existing = index.require(rel_path)
        verified_item = checksum.verify_checksum(real_path, existing.checksum)
        verified.append(
            manifest.ProvenancedChecksum(
                path=rel_path,
                checksum=verified_item.checksum,
                provenance=verified_item.provenance,
            )
        )
    return manifest.ChecksumIndex(verified)


def acquire_generated_checksums(paths):

    generated = []
    for rel_path, real_path in paths:
        item = checksum.generate_checksum(real_path)
        generated.append(
            manifest.ProvenancedChecksum(
                path=rel_path,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return manifest.ChecksumIndex(generated)
