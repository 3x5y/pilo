import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, call

from pilo import paths
from pilo.front import manifest
from pilo.front import rewrite
import pilotest


class TestRewriteCommand(pilotest.TestCase):

    @patch("sys.stdin", new_callable=StringIO)
    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        with pilotest.make_tmp_context() as cx:
            cx.args = []

            stdin.write("mv\tin/a\tin/b\n")
            stdin.seek(0)
            mod = pilotest.import_command("rewrite")

            with patch("pilo.context.Context", return_value=cx):
                mod.main()

            mock_parse.assert_called_once_with(["mv\tin/a\tin/b"])

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        with pilotest.make_tmp_context() as cx:
            cx.args = ["mv\tin/a\tin/b\nmv\tin/c\tin/d"]
            mod = pilotest.import_command("rewrite")

            with patch("pilo.context.Context", return_value=cx):
                mod.main()

            mock_parse.assert_called_once_with([
                "mv\tin/a\tin/b",
                "mv\tin/c\tin/d",
            ])

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        mod = pilotest.import_command("rewrite")

        with pilotest.tmpfile() as f:
            f.write_text("mv\tin/a\tin/b\n")
            path = str(f)
            with pilotest.make_tmp_context() as cx:
                cx.args = [path]
                with patch("pilo.context.Context", return_value=cx):
                    mod.main()

        mock_parse.assert_called_once_with(["mv\tin/a\tin/b"])
        Path(path).unlink(missing_ok=True)

    @patch("sys.stdin", new_callable=StringIO)
    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        stdin.write("mv\tin/stdin\tin/ignored\n")
        stdin.seek(0)
        mod = pilotest.import_command("rewrite")

        with pilotest.tmpfile() as f:
            f.write_text("mv\tin/file\tin/dst\n")
            path = str(f)
            with pilotest.make_tmp_context() as cx:
                cx.args = [path]
                with patch("pilo.context.Context", return_value=cx):
                    mod.main()

        mock_parse.assert_called_once_with(["mv\tin/file\tin/dst"])

    @patch("pilo.front.rewrite.parse_rewrite_ops")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        with pilotest.make_tmp_context() as cx:
            cx.args = ["mv\tin/a\tin/b\nmv\tin/c\tin/d"]
            mod = pilotest.import_command("rewrite")

            with patch("pilo.context.Context", return_value=cx):
                mod.main()

            mock_parse.assert_called_once_with([
                "mv\tin/a\tin/b",
                "mv\tin/c\tin/d",
            ])

    @patch("pilo.front.rewrite.RewriteScript.from_lines")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
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
        with pilotest.make_tmp_context() as cx:
            cx.args = ["mv\tin/a\tin/b"]

            script = unittest.mock.Mock()
            script.parse_ops.return_value = []
            mock_script.return_value = script

            mod = pilotest.import_command("rewrite")
            with patch("pilo.context.Context", return_value=cx):
                mod.main()

            mock_script.assert_called_once_with(["mv\tin/a\tin/b"])

            script.parse_ops.assert_called_once_with()

    @patch("builtins.print")
    @patch("pilo.front.rewrite.preview_rewrite_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_preview_mode(
        self,
        mock_build,
        mock_execute,
        mock_preview,
        mock_print,
    ):
        mock_preview.return_value = ["move /tmp/a -> /tmp/b"]

        cx = pilotest.make_context()
        cx.args = ["--preview", "mv\tin/a\tin/b"]
        mod = pilotest.import_command("rewrite")
        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_build.assert_called_once()
        mock_preview.assert_called_once()
        mock_execute.assert_not_called()
        mock_print.assert_called_once_with("move /tmp/a -> /tmp/b")

    @patch("pilo.front.manifest.execute_manifest_update_plan")
    @patch("pilo.front.manifest.build_manifest_update_plan")
    @patch("builtins.print")
    @patch("pilo.front.rewrite.preview_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_preview_mode_skips_manifest_updates(
        self,
        mock_build,
        mock_preview,
        mock_print,
        mock_manifest_build,
        mock_manifest_exec,
    ):
        cx = pilotest.make_context()
        cx.args = ["--preview", "mv\tin/a\tin/b"]

        mock_preview.return_value = []

        mod = pilotest.import_command("rewrite")
        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_manifest_build.assert_not_called()
        mock_manifest_exec.assert_not_called()

    @patch("builtins.print")
    @patch("pilo.front.rewrite.preview_rewrite_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_preview_mode_prints_multiple_lines(
        self,
        mock_build,
        mock_execute,
        mock_preview,
        mock_print,
    ):
        cx = pilotest.make_context()
        cx.args = [
            "--preview",
            "mv\tin/a\tin/b",
        ]
        mock_preview.return_value = [
            "move /tmp/a -> /tmp/b",
            "move /tmp/c -> /tmp/d",
        ]

        mod = pilotest.import_command("rewrite")
        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        arg_list = [
            call("move /tmp/a -> /tmp/b"),
            call("move /tmp/c -> /tmp/d"),
        ]
        self.assertEqual(mock_print.call_args_list, arg_list)


class TestRewriteValidateCommand(pilotest.TestCase):

    @patch("builtins.print")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_validate_command_builds_plan(
        self,
        mock_build,
        mock_print,
    ):
        cx = pilotest.make_context()
        cx.args = ["mv\tin/a\tin/b"]
        mod = pilotest.import_command("rewrite-validate")

        with patch("pilo.context.Context", return_value=cx):
            mod.main()

        mock_build.assert_called_once()

    @patch("builtins.print")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_validate_command_does_not_execute(
        self,
        mock_build,
        mock_execute,
        mock_print,
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


class TestRewriteScript(pilotest.TestCase):

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


class TestRewriteScriptVersioning(pilotest.TestCase):

    def test_parse_versioned_script(self):
        script = rewrite.RewriteScript.from_lines([
            "#version 1",
            "mv\tin/a\tin/b",
        ])

        ops = script.parse_ops()
        self.assertEqual(len(ops), 1)
        op = ops[0]
        self.assertEqual(op.kind, "mv")
        self.assertEqual(op.src, Path("in/a"))
        self.assertEqual(op.dst, Path("in/b"))

    def test_reject_unknown_script_version(self):
        script = rewrite.RewriteScript.from_lines([
            "#version 999",
            "mv\tin/a\tin/b",
        ])

        with pilotest.assert_fatal(self):
            script.parse_ops()

    def test_legacy_script_without_version_still_works(self):
        script = rewrite.RewriteScript.from_lines([
            "mv\tin/a\tin/b",
        ])

        ops = script.parse_ops()
        self.assertEqual(len(ops), 1)

    def test_script_version_header_not_treated_as_command(self):
        script = rewrite.RewriteScript.from_lines([
            "#version 1",
        ])

        ops = script.parse_ops()

        self.assertEqual(ops, [])

    def test_invalid_version_header_rejected(self):
        script = rewrite.RewriteScript.from_lines([
            "#version x",
        ])

        with pilotest.assert_fatal(self):
            script.parse_ops()


class TestRewriteScriptSerialization(pilotest.TestCase):

    def test_render_versioned_script(self):
        script = rewrite.RewriteScript.from_ops([
            rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            )
        ])

        lines = [
            "#version 1",
            "mv\tin/a\tin/b",
        ]
        self.assertEqual(script.render_lines(), lines)

    def test_render_empty_script(self):
        script = rewrite.RewriteScript.from_ops([])

        lines = [
            "#version 1",
        ]
        self.assertEqual(script.render_lines(), lines)

    def test_rewrite_script_serializes_remove(self):

        script = rewrite.RewriteScript.from_ops([
            rewrite.RewriteOp(
                kind="rm",
                src=Path("in/a.txt"),
                dst=None,
            )
        ])

        self.assertEqual(
            script.render_lines(),
            [
                "#version 1",
                "rm\tin/a.txt",
            ]
        )

class TestRewriteManifest(pilotest.TestCase):

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_rewrite_manifest_mutations_move(self, _):

        src = paths.Resolved(
            path=Path("/pile/in/old.txt"),
            dataset="tank/pile",
        )
        dst = paths.Resolved(
            path=Path("/pile/in/new.txt"),
            dataset="tank/pile",
        )
        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/old.txt"),
                dst=Path("in/new.txt"),
            ),
            src=src,
            dst=dst,
        )
        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/old.txt"),
            )
        ]
        muts = rewrite.build_manifest_mutations(
            [op],
            Path("/pile"),
            entries,
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(remove.subset, "pile")
        self.assertEqual(remove.path, Path("in/old.txt"))
        self.assertEqual(add.subset, "pile")
        self.assertEqual(add.entry.path, Path("in/new.txt"))
        self.assertEqual(add.entry.checksum, "abc123")

    def test_rewrite_manifest_mutations_reuse_checksum(self):

        entries = [
            manifest.ManifestEntry(
                checksum="existing",
                path=Path("in/old.txt"),
            )
        ]

        src = paths.Resolved(
            path=Path("/pile/in/old.txt"),
            dataset="tank/pile",
        )

        dst = paths.Resolved(
            path=Path("/pile/in/new.txt"),
            dataset="tank/pile",
        )

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/old.txt"),
                dst=Path("in/new.txt"),
            ),
            src=src,
            dst=dst,
        )

        muts = rewrite.build_manifest_mutations(
            [op],
            Path("/pile"),
            entries,
        )

        add = muts[1]

        self.assertEqual(
            add.entry.checksum,
            "existing",
        )
