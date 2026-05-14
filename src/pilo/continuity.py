from dataclasses import dataclass
from pathlib import Path

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


def build_continuity_transfers(mappings, verified):

    verified = manifest_model.as_verified_checksum_index(verified)
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


def continuity_manifest_mutations(transfers):

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
