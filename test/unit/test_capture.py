import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo import manifest
import pilotest


class TestCaptureManifest(unittest.TestCase):

    def test_generate_capture_manifest_lines(self):

        with pilotest.tmpdir() as td:
            root = td / "capture"
            root.mkdir()
            f = root / "a.txt"
            f.write_text("hello")

            lines = list(manifest.generate_manifest_lines(root))

            expected_hash = hashlib.sha256(b"hello").hexdigest()
            expected_lines = [f"{expected_hash}  ./a.txt"]
            self.assertEqual(lines, expected_lines)

    def test_write_capture_manifest(self):

        with pilotest.tmpdir() as td:

            root = td / "capture"
            root.mkdir()
            (root / "a.txt").write_text("aaa")
            out = root / "capture.manifest"
            cx = pilotest.make_context()
            manifest.write_manifest(
                cx,
                root,
                out,
            )

            self.assertTrue(out.exists())
            lines = out.read_text().splitlines()
            self.assertEqual(len(lines), 1)

    def test_verify_capture_manifest_lines_valid(self):

        with pilotest.tmpdir() as td:

            root = td / "capture"
            root.mkdir()
            path = root / "a.txt"
            path.write_text("hello")
            lines = list(manifest.generate_manifest_lines(root))

            self.assertTrue(
                manifest.verify_manifest_lines(
                    root,
                    lines,
                )
            )

    def test_verify_capture_manifest_lines_rejects_corruption(self):
        with pilotest.tmpdir() as td:

            root = td / "capture"
            root.mkdir()
            path = root / "a.txt"
            path.write_text("hello")
            lines = list(manifest.generate_manifest_lines(root))

            path.write_text("corrupt")

            self.assertFalse(
                manifest.verify_manifest_lines(
                    root,
                    lines,
                )
            )


class TestCaptureCommand(unittest.TestCase):

    @patch("pilo.checks.require_dataset", return_value=True)
    @patch("pilo.manifest.write_manifest")
    def test_capture_writes_manifest(self, mock_manifest, *_):
        mod = pilotest.import_command("capture")
        with pilotest.make_tmp_context() as cx:
            src = Path(cx.path) / "source.txt"
            src.write_text("hello")
            cx.args = [str(src)]
            cx.intake_path.mkdir()
            with patch("pilo.context.Context", return_value=cx):
                mod.main()
        mock_manifest.assert_called_once()

    @patch("pilo.checks.require_dataset", return_value=True)
    @patch("pilo.manifest.write_manifest")
    def test_manifest_written_inside_root(self, mock_manifest, *_):
        mod = pilotest.import_command("capture")

        with pilotest.make_tmp_context() as cx:
            cx.intake_path.mkdir()
            src = Path(cx.path) / "source.txt"
            src.write_text("hello")
            cx.args = [str(src)]
            with patch("pilo.context.Context", return_value=cx):
                mod.main()

        args = mock_manifest.call_args[0]
        manifest_path = args[2]
        self.assertEqual(manifest_path.name, "capture.manifest")
