import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pilo.front import rewrite
import pilotest


class TestRewriteCommand(unittest.TestCase):

    @patch("sys.stdin", new_callable=StringIO)
    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_reads_stdin_when_no_args(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_parse,
        stdin,
    ):
        cx = pilotest.make_context()

        stdin.write("mv\tin/a\tin/b\n")
        stdin.seek(0)

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(cx, "args", []):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_parse.assert_called_once_with([
            "mv\tin/a\tin/b"
        ])

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_compat_arg_transport(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_parse,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["mv\tin/a\tin/b\nmv\tin/c\tin/d"]
            ):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_parse.assert_called_once_with([
            "mv\tin/a\tin/b",
            "mv\tin/c\tin/d",
        ])

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_reads_script_file(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_parse,
    ):
        cx = pilotest.make_context()

        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("mv\tin/a\tin/b\n")
            path = f.name

        try:
            with patch("pilo.context.Context", return_value=cx):
                with patch.object(cx, "args", [path]):
                    mod = pilotest.import_command("rewrite")
                    mod.main()

            mock_parse.assert_called_once_with([
                "mv\tin/a\tin/b"
            ])

        finally:
            Path(path).unlink(missing_ok=True)

    @patch("sys.stdin", new_callable=StringIO)
    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_prefers_script_file_over_stdin(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_parse,
        stdin,
    ):
        cx = pilotest.make_context()

        stdin.write("mv\tin/stdin\tin/ignored\n")
        stdin.seek(0)

        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("mv\tin/file\tin/dst\n")
            path = f.name

        try:
            with patch("pilo.context.Context", return_value=cx):
                with patch.object(cx, "args", [path]):
                    mod = pilotest.import_command("rewrite")
                    mod.main()

            mock_parse.assert_called_once_with([
                "mv\tin/file\tin/dst"
            ])

        finally:
            Path(path).unlink(missing_ok=True)

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_preserves_inline_compatibility(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_parse,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["mv\tin/a\tin/b\nmv\tin/c\tin/d"]
            ):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_parse.assert_called_once_with([
            "mv\tin/a\tin/b",
            "mv\tin/c\tin/d",
        ])
