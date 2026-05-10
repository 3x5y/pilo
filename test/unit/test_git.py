import unittest
from unittest.mock import patch, Mock
from pathlib import Path

from pilo import git
import pilotest


class TestGitHelpers(unittest.TestCase):

    @patch("pilo.git.as_user")
    def test_git_commit_if_changed_adds_file(self, as_user):
        ok = Mock(returncode=0)
        dirty = Mock(returncode=1)

        as_user.side_effect = [
            ok,
            dirty,
            ok,
        ]

        cx = pilotest.make_context()

        git.commit_if_changed(
            cx,
            Path("/repo"),
            Path("/repo/file"),
            "msg",
        )

        calls = as_user.call_args_list

        self.assertEqual(
            calls[0].args[1][:4],
            ["git", "-C", "/repo", "add"],
        )

        self.assertEqual(
            calls[2].args[1][:4],
            ["git", "-C", "/repo", "commit"],
        )

    @patch("pilo.git.subprocess.run")
    def test_git_dirty_true(self, run):
        proc = Mock(returncode=1)
        run.return_value = proc

        result = git.is_dirty(Path("/repo"))

        self.assertEqual(result, True)
