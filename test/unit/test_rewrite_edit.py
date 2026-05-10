import unittest
from pathlib import Path
from unittest.mock import patch

import pilotest


class TestRewriteEdit(unittest.TestCase):

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
