import hashlib
import tempfile
import unittest
from pathlib import Path

import pilo


class TestManifest(unittest.TestCase):

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_bytes(b"hello world")

            expected = hashlib.sha256(
                b"hello world"
            ).hexdigest()

            self.assertEqual(
                pilo.sha256_file(path),
                expected,
            )

    def test_sha256_file_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty"

            path.write_bytes(b"")

            expected = hashlib.sha256(b"").hexdigest()

            self.assertEqual(
                pilo.sha256_file(path),
                expected,
            )

    def test_generate_manifest_lines_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            (root / "z.txt").write_text("z")
            (root / "a.txt").write_text("a")

            lines = list(
                pilo.generate_manifest_lines(root)
            )

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

            lines = list(
                pilo.generate_manifest_lines(root)
            )

            self.assertEqual(len(lines), 1)

            line = lines[0]

            self.assertTrue(
                line.endswith("  ./dir/x.txt")
            )

    def test_generate_manifest_lines_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            lines = list(
                pilo.generate_manifest_lines(root)
            )

            self.assertEqual(lines, [])

    def test_verify_manifest_lines_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            f = root / "a.txt"
            f.write_text("abc")

            lines = list(
                pilo.generate_manifest_lines(root)
            )

            self.assertTrue(
                pilo.verify_manifest_lines(root, lines)
            )

    def test_verify_manifest_lines_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            f = root / "a.txt"
            f.write_text("abc")

            lines = list(
                pilo.generate_manifest_lines(root)
            )

            f.write_text("changed")

            self.assertFalse(
                pilo.verify_manifest_lines(root, lines)
            )

    def test_verify_manifest_lines_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            f = root / "a.txt"
            f.write_text("abc")

            lines = list(
                pilo.generate_manifest_lines(root)
            )

            f.unlink()

            self.assertFalse(
                pilo.verify_manifest_lines(root, lines)
            )
