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

    @patch("pilo.front.rewrite.RewriteScript.from_lines")
    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_uses_script_model(
        self,
        mock_build,
        mock_execute,
        mock_manifest_build,
        mock_manifest_exec,
        mock_script,
    ):
        cx = pilotest.make_context()

        script = unittest.mock.Mock()
        script.parse_ops.return_value = []

        mock_script.return_value = script

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["mv\tin/a\tin/b"]
            ):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_script.assert_called_once_with([
            "mv\tin/a\tin/b"
        ])

        script.parse_ops.assert_called_once_with()

class TestRewriteScript(unittest.TestCase):

    def test_script_from_lines(self):
        script = rewrite.RewriteScript.from_lines([
            "mv\tin/a\tin/b",
            "mv\tin/c\tin/d",
        ])

        self.assertEqual(
            script.lines,
            [
                "mv\tin/a\tin/b",
                "mv\tin/c\tin/d",
            ]
        )

    def test_script_parse_ops(self):
        script = rewrite.RewriteScript.from_lines([
            "mv\tin/a\tin/b"
        ])

        ops = script.parse_ops()

        self.assertEqual(len(ops), 1)

        op = ops[0]

        self.assertEqual(op.kind, "mv")
        self.assertEqual(op.src, Path("in/a"))
        self.assertEqual(op.dst, Path("in/b"))

    def test_script_ignores_blank_lines(self):
        script = rewrite.RewriteScript.from_lines([
            "",
            "   ",
            "mv\tin/a\tin/b",
        ])

        ops = script.parse_ops()

        self.assertEqual(len(ops), 1)


class TestRewriteValidateCommand(unittest.TestCase):

    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_validate_command_builds_plan(
        self,
        mock_build,
    ):
        cx = pilotest.make_context()
        cx.args = ["mv\tin/a\tin/b"]
        mod = pilotest.import_command("rewrite-validate")

        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_build.assert_called_once()

    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_validate_command_does_not_execute(
        self,
        mock_build,
        mock_execute,
    ):
        cx = pilotest.make_context()
        cx.args = ["mv\tin/a\tin/b"]
        mod = pilotest.import_command("rewrite-validate")

        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_execute.assert_not_called()

    @patch("builtins.print")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_validate_command_prints_ok(
        self,
        mock_build,
        mock_print,
    ):
        cx = pilotest.make_context()
        cx.args = ["mv\tin/a\tin/b"]
        mod = pilotest.import_command("rewrite-validate")

        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_print.assert_called_once_with("valid")

    def test_validate_command_rejects_invalid_script(self):
        cx = pilotest.make_context()
        cx.args = ["invalid"]
        mod = pilotest.import_command("rewrite-validate")

        with patch("pilo.context.Context", return_value=cx):
            with pilotest.assert_fatal(self):
                mod.main()
