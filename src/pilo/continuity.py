from dataclasses import dataclass
from pathlib import Path

from . import manifest_model


@dataclass(frozen=True)
class ContinuityTransfer:

    src: Path
    dst: Path
    checksum: str
    provenance: manifest_model.ChecksumProvenance


def build_continuity_transfers(mappings, verified):

    verified = manifest_model.as_verified_checksum_index(verified)
    transfers = []

    for src, dst in mappings:
        item = verified.require(src)
        transfers.append(
            ContinuityTransfer(
                src=src,
                dst=dst,
                checksum=item.checksum,
                provenance=item.provenance,
            )
        )
    return transfers


def continuity_manifest_mutations(subset, transfers):

    muts = []

    for transfer in transfers:
        muts.append(
            manifest_model.ManifestRemoveEntry(
                subset=subset,
                path=transfer.src,
            )
        )
        muts.append(
            manifest_model.ManifestAddEntry(
                subset=subset,
                entry=manifest_model.ManifestEntry(
                    checksum=transfer.checksum,
                    path=transfer.dst,
                )
            )
        )
    return muts
