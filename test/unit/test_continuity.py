import unittest
from pathlib import Path

from pilo.content import manifest
import pilotest


class TestContinuity(pilotest.TestCase):

    def test_build_transfer_mutations_same_subset(self):

        muts = manifest.build_transfer_mutations(
            [
                manifest.ContinuityMapping(
                    src_subset="pile",
                    dst_subset="pile",
                    src=Path("in/a.txt"),
                    dst=Path("in/b.txt"),
                    checksum="abc123",
                )
            ]
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(remove.subset, "pile")
        self.assertEqual(remove.path, Path("in/a.txt"))
        self.assertEqual(add.subset, "pile")
        self.assertEqual(add.entry.path, Path("in/b.txt"))
        self.assertEqual(add.entry.checksum, "abc123")

    def test_build_transfer_mutations_cross_subset(self):

        muts = manifest.build_transfer_mutations(
            [
                manifest.ContinuityMapping(
                    src_subset="pile",
                    dst_subset="collection",
                    src=Path("out/collection/a.txt"),
                    dst=Path("a.txt"),
                    checksum="abc123",
                )
            ]
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(remove.subset, "pile")
        self.assertEqual(remove.path, Path("out/collection/a.txt"))
        self.assertEqual(add.subset, "collection")
        self.assertEqual(add.entry.path, Path("a.txt"))
        self.assertEqual(add.entry.checksum, "abc123")

    def test_build_transfer_mutations_destination_uses_mapping_checksum(self):

        mappings = [
            manifest.ContinuityMapping(
                src_subset="pile",
                dst_subset="filing",
                src=Path("a.txt"),
                dst=Path("b.txt"),
                checksum="mapping-hash",
            )
        ]

        muts = manifest.build_transfer_mutations(mappings)

        self.assertEqual(muts[1].entry.checksum, "mapping-hash")

    def test_build_transfer_mutations_empty_mappings(self):

        muts = manifest.build_transfer_mutations([])

        self.assertEqual(muts, [])