import unittest
from pathlib import Path

from pilo.content import continuity
from pilo.front import manifest
import pilotest


class TestContinuity(pilotest.TestCase):

    def test_build_continuity_transfers(self):

        verified = (
            manifest.ChecksumIndex([
                manifest.ProvenancedChecksum(
                    path=Path("in/a.txt"),
                    checksum="abc123",
                    provenance=(
                        manifest
                        .ChecksumProvenance
                        .VERIFIED
                    ),
                )
            ])
        )

        transfers = (
            continuity
            .build_transfers(
                [
                    continuity.ContinuityMapping(
                        src_subset="pile",
                        dst_subset="pile",
                        src=Path("in/a.txt"),
                        dst=Path("in/b.txt"),
                    )
                ],
                verified,
            )
        )

        self.assertEqual(len(transfers), 1)

        transfer = transfers[0]

        self.assertEqual(transfer.src, Path("in/a.txt"))
        self.assertEqual(transfer.dst, Path("in/b.txt"))
        self.assertEqual(transfer.checksum, "abc123")

    def test_continuity_manifest_mutations(self):

        transfers = [
            continuity.ContinuityTransfer(
                src_subset="pile",
                dst_subset="pile",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        ]

        muts = continuity.build_mutations(transfers)

        self.assertEqual(len(muts), 2)
        remove = muts[0]
        add = muts[1]
        self.assertEqual(remove.path, Path("in/a.txt"))
        self.assertEqual(add.entry.path, Path("in/b.txt"))
        self.assertEqual(add.entry.checksum, "abc123")

    def test_build_continuity_transfers_uses_mapping_objects(self):

        mapping = continuity.ContinuityMapping(
            src=Path("a.txt"),
            dst=Path("b.txt"),
            src_subset="pile",
            dst_subset="pile",
        )
        mappings = [mapping]
        provenance = manifest.ChecksumProvenance.VERIFIED
        checksum = manifest.ProvenancedChecksum(
            path=Path("a.txt"),
            checksum="abc123",
            provenance=provenance,
        )
        verified = manifest.ChecksumIndex([checksum])

        transfers = continuity.build_transfers(mappings, verified)

        self.assertEqual(len(transfers), 1)
        transfer = transfers[0]
        self.assertEqual(transfer.src, Path("a.txt"))
        self.assertEqual(transfer.dst, Path("b.txt"))
        self.assertEqual(transfer.checksum, "abc123")

    def test_continuity_manifest_mutations_same_subset(self):

        transfers = [
            continuity.ContinuityTransfer(
                src_subset="pile",
                dst_subset="pile",
                src=Path("a.txt"),
                dst=Path("b.txt"),
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        ]

        muts = continuity.build_mutations(transfers)

        self.assertEqual(len(muts), 2)
        self.assertEqual(muts[0].subset, "pile")
        self.assertEqual(muts[1].subset, "pile")

    def test_continuity_manifest_mutations_cross_subset(self):

        transfers = [
            continuity.ContinuityTransfer(
                src_subset="pile",
                dst_subset="collection",
                src=Path(
                    "out/collection/a.txt"
                ),
                dst=Path("a.txt"),
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        ]

        muts = continuity.build_mutations(transfers)

        self.assertEqual(len(muts), 2)
        remove = muts[0]
        add = muts[1]
        self.assertEqual(remove.subset, "pile")
        self.assertEqual(remove.path, Path("out/collection/a.txt"))
        self.assertEqual(add.subset, "collection")
        self.assertEqual(add.entry.path, Path("a.txt"))
        self.assertEqual(add.entry.checksum, "abc123")
