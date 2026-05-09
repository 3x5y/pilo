import hashlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pilo import fs, manifest, status
from pilo.front import manifest_verify
import pilotest


class TestManifest(unittest.TestCase):

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_bytes(b"hello world")

            expected = hashlib.sha256(b"hello world").hexdigest()

            self.assertEqual(fs.sha256_file(path), expected)

    def test_sha256_file_empty(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty"
            path.write_bytes(b"")

            expected = hashlib.sha256(b"").hexdigest()

            self.assertEqual(fs.sha256_file(path), expected)

    def test_generate_manifest_lines_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "z.txt").write_text("z")
            (root / "a.txt").write_text("a")

            lines = list(manifest.generate_manifest_lines(root))

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

            lines = list(manifest.generate_manifest_lines(root))

            self.assertEqual(len(lines), 1)
            line = lines[0]
            self.assertTrue(line.endswith("  ./dir/x.txt"))

    def test_generate_manifest_lines_empty_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            lines = list(manifest.generate_manifest_lines(root))

            self.assertEqual(lines, [])

    def test_verify_manifest_lines_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))

            self.assertTrue(manifest.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))
            f.write_text("changed")

            self.assertFalse(manifest.verify_manifest_lines(root, lines))

    def test_verify_manifest_lines_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / "a.txt"
            f.write_text("abc")
            lines = list(manifest.generate_manifest_lines(root))

            f.unlink()

            self.assertFalse(manifest.verify_manifest_lines(root, lines))

    def test_manifest_verify_op_model(self):
        op = manifest_verify.ManifestVerifyOp(
            subset="pile",
            root=Path("/tmp/pile"),
            manifest=Path("/tmp/admin/manifest/pile.manifest"),
        )

        self.assertEqual(op.subset, "pile")
        self.assertEqual(op.root, Path("/tmp/pile"))
        self.assertEqual(op.manifest, Path("/tmp/admin/manifest/pile.manifest"))

    def test_build_manifest_verify_plan(self):
        cx = pilotest.make_context()

        ops = manifest_verify.build_manifest_verify_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(len(ops), 2)
        self.assertEqual(ops[0].root, cx.pile_path)
        self.assertEqual(ops[1].root, cx.static_path / "collection")
        self.assertEqual(ops[0].manifest, cx.admin_path / "manifest/pile.manifest")

    @patch("subprocess.run")
    def test_verify_manifest_op(self, mock_run):
        op = manifest_verify.ManifestVerifyOp(
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

                manifest_verify.verify_manifest_op(op)

        mock_run.assert_called_once()

    @patch("pilo.front.manifest_verify.verify_manifest_op")
    def test_execute_manifest_verify_plan(
        self,
        mock_verify,
    ):
        ops = [
            manifest_verify.ManifestVerifyOp(
                subset="pile",
                root=Path("/tmp/pile"),
                manifest=Path("/tmp/pile.manifest"),
            )
        ]

        manifest_verify.execute_manifest_verify_plan(ops)

        mock_verify.assert_called_once()

    @patch("subprocess.run")
    def test_verify_manifest_failure_raises_fatal(
        self,
        mock_run,
    ):
        op = manifest_verify.ManifestVerifyOp(
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
                    manifest_verify.verify_manifest_op(op)

    @patch("sys.exit")
    @patch("pilo.status.render_system_status")
    @patch("pilo.status.check_manifest_status")
    def test_manifest_verify_uses_status_system(
        self,
        mock_check,
        mock_render,
        mock_exit,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command(
                "manifest-verify"
            )

            mod.main()

        mock_check.assert_called_once()
        mock_render.assert_called_once()
        mock_exit.assert_called_once()

    @patch("sys.exit")
    @patch("pilo.status.render_system_status")
    def test_manifest_verify_returns_status_code(
        self,
        mock_render,
        mock_exit,
    ):
        cx = pilotest.make_context()

        st = status.SystemStatus()
        st.code = 1

        with patch("pilo.context.Context", return_value=cx):
            with patch(
                "pilo.status.check_manifest_status",
                side_effect=lambda cx, s: setattr(s, "code", 1),
            ):
                mod = pilotest.import_command(
                    "manifest-verify"
                )

                mod.main()

        mock_exit.assert_called_once_with(1)

    @patch("builtins.print")
    @patch("sys.exit")
    @patch("pilo.status.check_manifest_status")
    @patch(
        "pilo.status.render_system_status",
        return_value=["OK: manifest: pile verified"],
    )
    def test_manifest_verify_renders_messages(
        self,
        mock_render,
        mock_check,
        mock_exit,
        mock_print,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command(
                "manifest-verify"
            )

            mod.main()

        mock_print.assert_called_once_with(
            "OK: manifest: pile verified"
        )
