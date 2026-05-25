from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilo import checks
from pilo.content import manifest
import pilotest


class TestChecks(pilotest.TestCase):

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_require_dataset_ok(self, _):
        checks.require_dataset("tank/foo")

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_require_dataset_missing(self, _):
        with pilotest.assert_fatal(self):
            checks.require_dataset("tank/foo")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_require_snapshot_ok(self, _):
        checks.require_snapshot("tank/a@snap")

    @patch("pilo.zfs.snapshot_exists", return_value=False)
    def test_require_snapshot_missing(self, _):
        with pilotest.assert_fatal(self):
            checks.require_snapshot("tank/a@snap")

    def test_require_file_accepts_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_text("x")

            checks.require_file(path)

    def test_require_file_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missing.txt"

            with pilotest.assert_fatal(self):
                checks.require_file(path)

    def test_require_no_conflict_accepts_missing_target(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("x")

            checks.require_no_conflict(src, dst)

    def test_require_no_conflict_accepts_identical_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("same")
            dst.write_text("same")

            checks.require_no_conflict(src, dst)

    def test_require_no_conflict_rejects_different_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("a")
            dst.write_text("b")

            with pilotest.assert_fatal(self):
                checks.require_no_conflict(src, dst)

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_valid_require_dataset_ok(self, _):
        checks.require_dataset("tank/foo")

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_valid_require_dataset_missing(self, _):
        with pilotest.assert_fatal(self):
            checks.require_dataset("tank/foo")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_valid_require_snapshot_ok(self, _):
        checks.require_snapshot("tank/a@snap")

    @patch("pilo.zfs.snapshot_exists", return_value=False)
    def test_valid_require_snapshot_missing(self, _):
        with pilotest.assert_fatal(self):
            checks.require_snapshot("tank/a@snap")

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_valid_require_new_dataset_ok(self, _):
        checks.require_new_dataset("tank/a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_valid_require_new_dataset_fail(self, _):
        with pilotest.assert_fatal(self):
            checks.require_new_dataset("tank/a")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_valid_valid_snapshot(self, _):
        checks.require_snapshot_of_dataset("tank/a@r1", "tank/a")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_valid_wrong_dataset_fails(self, _):
        with pilotest.assert_fatal(self):
            checks.require_snapshot_of_dataset("tank/b@r1", "tank/a")

    def test_valid_valid_within(self):
        checks.require_within_dataset("tank/a/foo", "tank/a")

    def test_valid_invalid_within(self):
        with pilotest.assert_fatal(self):
            checks.require_within_dataset("tank/b/foo", "tank/a")

    def test_valid_require_file_accepts_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_text("x")

            checks.require_file(path)

    def test_valid_require_file_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missing.txt"

            with pilotest.assert_fatal(self):
                checks.require_file(path)

    def test_valid_require_no_conflict_accepts_missing_target(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("x")

            checks.require_no_conflict(src, dst)

    def test_valid_require_no_conflict_accepts_identical_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("same")
            dst.write_text("same")

            checks.require_no_conflict(src, dst)

    def test_valid_require_no_conflict_rejects_different_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("a")
            dst.write_text("b")

            with pilotest.assert_fatal(self):
                checks.require_no_conflict(src, dst)

    def test_require_verified_accepts_verified(self):

        item = (
            manifest.ProvenancedChecksum(
                path=Path("a.txt"),
                checksum="abc",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        )

        checks.require_verified(item)

    def test_require_verified_rejects_generated(self):

        item = (
            manifest.ProvenancedChecksum(
                path=Path("a.txt"),
                checksum="abc",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .GENERATED
                ),
            )
        )

        with pilotest.assert_fatal(self):
            checks.require_verified(item)
