import unittest
from pathlib import Path
from unittest.mock import patch
from io import StringIO
from unittest.mock import mock_open

import pilotest


class TestRewriteEdit(pilotest.TestCase):

    def test_build_script_lines(self):
        mod = pilotest.import_command("rewrite-edit")

        before = [
            "in/a.txt",
            "in/b.txt",
        ]

        after = [
            "in/a-renamed.txt",
            "in/b.txt",
        ]

        lines = list(
            mod.build_script_lines(before, after)
        )

        self.assertEqual(
            lines,
            [
                "mv\tin/a.txt\tin/a-renamed.txt",
            ]
        )

    def test_parse_edited_lines(self):
        mod = pilotest.import_command("rewrite-edit")

        result = mod.parse_edited_lines([
            "in/a.txt",
            "",
            "  ",
            "in/b.txt ",
        ])

        self.assertEqual(
            result,
            [
                "in/a.txt",
                "in/b.txt",
            ]
        )

    @patch("subprocess.run")
    def test_interactive_uses_explicit_phases(
        self,
        mock_run,
    ):
        cx = pilotest.make_context()
        tmp = Path("/tmp/edit-buffer")
        mod = pilotest.import_command("rewrite-edit")
        def test():
            mock_list.return_value = ["in/a.txt"]
            mock_write.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]

            with patch("sys.exit"):
                mod.interactive(cx)

            mock_list.assert_called_once_with(cx)
            mock_write.assert_called_once_with(["in/a.txt"])
            mock_edit.assert_called_once_with(tmp)
            mock_run.assert_called_once()

        with patch.object(mod, 'list_files') as mock_list:
            with patch.object(mod, 'write_edit_buffer') as mock_write:
                with patch.object(mod, 'edit_file') as mock_edit:
                    test()

    def test_generate_script_preserves_duplicate_detection(self):
        mod = pilotest.import_command("rewrite-edit")

        before = [
            "in/a",
            "in/b",
        ]

        after = [
            "in/x",
            "in/x",
        ]

        with pilotest.assert_fatal(self):
            list(mod.build_script_lines(before, after))

    @patch("builtins.open", new_callable=mock_open)
    def test_write_script_file(
        self,
        mock_file,
    ):
        mod = pilotest.import_command("rewrite-edit")

        script = "\n".join([
            "mv\tin/a\tin/b",
            "mv\tin/c\tin/d",
        ])

        mod.write_script_file(
            "/tmp/test-script.pilo",
            script,
        )

        mock_file.assert_called_once_with(
            "/tmp/test-script.pilo",
            "w",
        )

        handle = mock_file()

        handle.write.assert_called_once_with(script)

    #@patch("pilo-rewrite-edit.execute_script")
    #@patch("pilo-rewrite-edit.write_script_file")
    #@patch("pilo-rewrite-edit.edit_file")
    #@patch("pilo-rewrite-edit.write_edit_buffer")
    #@patch("pilo-rewrite-edit.list_files")
    def test_interactive_output_script_skips_execution(
        self,
        #mock_list,
        #mock_write_buffer,
        #mock_edit,
        #mock_write_script,
        #mock_execute,
    ):
        mod = pilotest.import_command("rewrite-edit")
        cx = pilotest.make_context()
        cx.args = [
            "--output-script",
            "/tmp/changes.pilo",
        ]
        tmp = Path("/tmp/edit-buffer")

        def test():
            mock_list.return_value = ["in/a.txt"]
            mock_write_buffer.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]

            with patch("sys.exit") as mock_exit:
                mod.interactive(cx)

            mock_write_script.assert_called_once()
            mock_execute.assert_not_called()

        with patch.object(mod, 'execute_script') as mock_execute:
            with patch.object(mod, 'write_script_file') as mock_write_script:
                with patch.object(mod, 'edit_file') as mock_edit:
                    with patch.object(mod, 'write_edit_buffer') as mock_write_buffer:
                        with patch.object(mod, 'list_files') as mock_list:
                            test()

    #@patch("pilo-rewrite-edit.execute_script")
    #@patch("pilo-rewrite-edit.edit_file")
    #@patch("pilo-rewrite-edit.write_edit_buffer")
    #@patch("pilo-rewrite-edit.list_files")
    def test_interactive_default_executes_script(
        self,
        #mock_list,
        #mock_write_buffer,
        #mock_edit,
        #mock_execute,
    ):
        mod = pilotest.import_command("rewrite-edit")
        cx = pilotest.make_context()
        tmp = Path("/tmp/edit-buffer")

        def test():
            mock_list.return_value = ["in/a.txt"]
            mock_write_buffer.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]
            result = unittest.mock.Mock()
            result.returncode = 0
            mock_execute.return_value = result

            with patch("sys.exit") as mock_exit:
                mod.interactive(cx)

            mock_execute.assert_called_once()
            mock_exit.assert_called_once_with(0)

        with patch.object(mod, 'execute_script') as mock_execute:
            with patch.object(mod, 'edit_file') as mock_edit:
                with patch.object(mod, 'write_edit_buffer') as mock_write_buffer:
                    with patch.object(mod, 'list_files') as mock_list:
                        test()

    def test_output_script_path_argument(self):
        mod = pilotest.import_command("rewrite-edit")

        cx = pilotest.make_context()

        cx.args = [
            "--output-script",
            "/tmp/test.pilo",
        ]

        self.assertEqual(
            mod.output_script_path(cx),
            "/tmp/test.pilo",
        )

    def test_output_script_path_missing_argument(self):
        mod = pilotest.import_command("rewrite-edit")

        cx = pilotest.make_context()

        cx.args = [
            "--output-script",
        ]

        with pilotest.assert_fatal(self):
            mod.output_script_path(cx)

    def test_has_apply_flag(self):
        mod = pilotest.import_command("rewrite-edit")

        cx = pilotest.make_context()

        cx.args = ["--apply"]

        self.assertTrue(
            mod.has_apply(cx)
        )

    def test_has_apply_flag_false(self):
        mod = pilotest.import_command("rewrite-edit")

        cx = pilotest.make_context()

        self.assertFalse(
            mod.has_apply(cx)
        )

    #@patch("pilo-rewrite-edit.execute_script")
    #@patch("pilo-rewrite-edit.edit_file")
    #@patch("pilo-rewrite-edit.write_edit_buffer")
    #@patch("pilo-rewrite-edit.list_files")
    def test_apply_flag_executes_script(
        self,
        #mock_list,
        #mock_write_buffer,
        #mock_edit,
        #mock_execute,
    ):
        mod = pilotest.import_command("rewrite-edit")
        cx = pilotest.make_context()
        cx.args = ["--apply"]
        tmp = Path("/tmp/edit-buffer")

        def test():
            mock_list.return_value = ["in/a.txt"]
            mock_write_buffer.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]
            result = unittest.mock.Mock()
            result.returncode = 0
            mock_execute.return_value = result

            with patch("sys.exit") as mock_exit:
                mod.interactive(cx)

            mock_execute.assert_called_once()
            mock_exit.assert_called_once_with(0)

        with patch.object(mod, 'execute_script') as mock_execute:
            with patch.object(mod, 'edit_file') as mock_edit:
                with patch.object(mod, 'write_edit_buffer') as mock_write_buffer:
                    with patch.object(mod, 'list_files') as mock_list:
                        test()

    #@patch("pilo-rewrite-edit.execute_script")
    #@patch("pilo-rewrite-edit.write_script_file")
    #@patch("pilo-rewrite-edit.edit_file")
    #@patch("pilo-rewrite-edit.write_edit_buffer")
    #@patch("pilo-rewrite-edit.list_files")
    def test_output_script_without_apply_skips_execution(
        self,
        #mock_list,
        #mock_write_buffer,
        #mock_edit,
        #mock_write_script,
        #mock_execute,
    ):
        mod = pilotest.import_command("rewrite-edit")
        cx = pilotest.make_context()
        cx.args = [
            "--output-script",
            "/tmp/changes.pilo",
        ]
        tmp = Path("/tmp/edit-buffer")

        def test():
            mock_list.return_value = ["in/a.txt"]
            mock_write_buffer.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]
            mod.interactive(cx)
            mock_write_script.assert_called_once()
            mock_execute.assert_not_called()

        with patch.object(mod, 'execute_script') as mock_execute:
            with patch.object(mod, 'write_script_file') as mock_write_script:
                with patch.object(mod, 'edit_file') as mock_edit:
                    with patch.object(mod, 'write_edit_buffer') as mock_write_buffer:
                        with patch.object(mod, 'list_files') as mock_list:
                            test()

    #@patch("pilo-rewrite-edit.execute_script")
    #@patch("pilo-rewrite-edit.write_script_file")
    #@patch("pilo-rewrite-edit.edit_file")
    #@patch("pilo-rewrite-edit.write_edit_buffer")
    #@patch("pilo-rewrite-edit.list_files")
    def test_output_script_with_apply_executes_script(
        self,
        #mock_list,
        #mock_write_buffer,
        #mock_edit,
        #mock_write_script,
        #mock_execute,
    ):
        mod = pilotest.import_command("rewrite-edit")
        tmp = Path("/tmp/edit-buffer")
        cx = pilotest.make_context()
        cx.args = [
            "--output-script",
            "/tmp/changes.pilo",
            "--apply",
        ]
        def test():

            mock_list.return_value = ["in/a.txt"]
            mock_write_buffer.return_value = tmp
            mock_edit.return_value = ["in/b.txt"]
            result = unittest.mock.Mock()
            result.returncode = 0
            mock_execute.return_value = result

            with patch("sys.exit") as mock_exit:
                mod.interactive(cx)

            mock_write_script.assert_called_once()
            mock_execute.assert_called_once()
            mock_exit.assert_called_once_with(0)
        with patch.object(mod, 'execute_script') as mock_execute:
            with patch.object(mod, 'write_script_file') as mock_write_script:
                with patch.object(mod, 'edit_file') as mock_edit:
                    with patch.object(mod, 'write_edit_buffer') as mock_write_buffer:
                        with patch.object(mod, 'list_files') as mock_list:
                            test()
