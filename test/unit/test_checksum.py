import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.front import checksum
from pilo import manifest_model
import pilotest


class TestChecksum(pilotest.TestCase):

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_generate_checksum_marks_generated(self, mock_sha):
        item = checksum.generate_checksum(Path("/tmp/a.txt"))
        self.assertEqual(item.checksum, "abc123")

        self.assertEqual(
            item.provenance,
            (
                manifest_model
                .ChecksumProvenance
                .GENERATED
            ),
        )

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_verify_checksum_marks_verified(self, mock_sha):
        item = checksum.verify_checksum(Path("/tmp/a.txt"), "abc123")

        self.assertEqual(
            item.provenance,
            (
                manifest_model
                .ChecksumProvenance
                .VERIFIED
            ),
        )

    @patch("pilo.fs.sha256_file", return_value="wrong")
    def test_verify_checksum_rejects_mismatch(self, mock_sha):
        with pilotest.assert_fatal(self):
            checksum.verify_checksum(
                Path("/tmp/a.txt"),
                "expected",
            )
