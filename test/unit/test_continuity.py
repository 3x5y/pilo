import unittest
from pathlib import Path

from pilo import continuity
from pilo import manifest_model


class TestContinuity(unittest.TestCase):

    def test_build_continuity_transfers(self):

        verified = (
            manifest_model.VerifiedChecksumIndex([
                manifest_model.ProvenancedChecksum(
                    path=Path("in/a.txt"),
                    checksum="abc123",
                    provenance=(
                        manifest_model
                        .ChecksumProvenance
                        .VERIFIED
                    ),
                )
            ])
        )

        transfers = (
            continuity
            .build_continuity_transfers(
                [
                    continuity.ContinuityMapping(
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
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
                checksum="abc123",
                provenance=(
                    manifest_model
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        ]

        muts = (
            continuity
            .continuity_manifest_mutations(
                "pile",
                transfers,
            )
        )

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
        )
        mappings = [mapping]
        provenance = manifest_model.ChecksumProvenance.VERIFIED
        checksum = manifest_model.ProvenancedChecksum(
            path=Path("a.txt"),
            checksum="abc123",
            provenance=provenance,
        )
        verified = manifest_model.VerifiedChecksumIndex([checksum])

        transfers = continuity.build_continuity_transfers(mappings, verified)

        self.assertEqual(len(transfers), 1)
        transfer = transfers[0]
        self.assertEqual(transfer.src, Path("a.txt"))
        self.assertEqual(transfer.dst, Path("b.txt"))
        self.assertEqual(transfer.checksum, "abc123")
