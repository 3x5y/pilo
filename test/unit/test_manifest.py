import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import pilo
import pilotest


class TestManifest(unittest.TestCase):

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_bytes(b"hello world")

            expected = hashlib.sha256(b"hello world").hexdigest()

            self.assertEqual(pilo.sha256_file(path), expected)

    def test_sha256_file_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty"
            path.write_bytes(b"")

            expected = hashlib.sha256(b"").hexdigest()

            self.assertEqual(pilo.sha256_file(path), expected)

    def test_generate_manifest_lines_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "z.txt").write_text("z")
            (root / "a.txt").write_text("a")

            lines = list(pilo.generate_manifest_lines(root))

            self.assertEqual(
                [line.split("  ./")[1] for line in lines],
                ["a.txt", "z.txt"],
            )

    def test_generate_manifest_lines_relative_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sub = root / "dir"
            sub.mkdir()
            f = sub / "x.txt"
            f.write_text("abc")

            lines = list(pilo.generate_manifest_lines(root))

            self.assertEqual(len(lines), 1)
            line = lines[0]
            self.assertTrue(line.endswith("  ./dir/x.txt"))

    def test_generate_manifest_lines_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            lines = list(pilo.generate_manifest_lines(root))

            self.assertEqual(lines, [])

    def test_verify_manifest_lines_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(pilo.generate_manifest_lines(root))

            self.assertTrue(pilo.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(pilo.generate_manifest_lines(root))
            f.write_text("changed")

            self.assertFalse(pilo.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(pilo.generate_manifest_lines(root))

            f.unlink()

            self.assertFalse(pilo.verify_manifest_lines(root, lines))

    def test_manifest_verify_op_model(self):
        op = pilo.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/admin/manifest/pile.manifest"),
        )

        self.assertEqual(op.subset, "pile")
        self.assertEqual(op.root, Path("/tmp/pile"))
        self.assertEqual(op.manifest, Path("/tmp/admin/manifest/pile.manifest"))

    def test_build_manifest_verify_plan(self):
        cx = pilotest.make_context()

        ops = pilo.build_manifest_verify_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(len(ops), 2)
        self.assertEqual(ops[0].root, cx.pile_path)
        self.assertEqual(ops[1].root, cx.static_path / "collection")
        self.assertEqual(ops[0].manifest, cx.admin_path / "manifest/pile.manifest")

    @patch("subprocess.run")
    def test_verify_manifest_op(self, mock_run):
        op = pilo.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/pile.manifest"),
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(
                Path,
                "stat",
            ) as mock_stat:

                mock_stat.return_value.st_size = 123

                pilo.verify_manifest_op(op)

        mock_run.assert_called_once()

    @patch("pilo.verify_manifest_op")
    def test_execute_manifest_verify_plan(
        self,
        mock_verify,
    ):
        ops = [
            pilo.ManifestVerifyOp(
                subset="pile",
                root=Path("/tmp/pile"),
                manifest=Path("/tmp/pile.manifest"),
            )
        ]

        pilo.execute_manifest_verify_plan(ops)

        mock_verify.assert_called_once()

    @patch("subprocess.run")
    def test_verify_manifest_failure_raises_fatal(
        self,
        mock_run,
    ):
        op = pilo.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/pile.manifest"),
        )

        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["sha256sum"],
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(Path, "stat") as mock_stat:

                mock_stat.return_value.st_size = 1

                with pilotest.assert_fatal(self):
                    pilo.verify_manifest_op(op)
