import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pilo
import pilotest


class TestManifestPlan(unittest.TestCase):

    def test_manifest_subset_root(self):
        cx = pilotest.make_context()

        self.assertEqual(
            pilo.manifest_subset_root(cx, "pile"),
            cx.pile_path,
        )

        self.assertEqual(
            pilo.manifest_subset_root(cx, "collection"),
            cx.static_path / "collection",
        )

        self.assertEqual(
            pilo.manifest_subset_root(cx, "filing"),
            cx.static_path / "filing",
        )

    def test_build_manifest_update_plan(self):
        cx = pilotest.make_context()

        plan = pilo.build_manifest_update_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(
            [s.name for s in plan.subsets],
            ["pile", "collection"]
        )

    @patch("pilo.write_manifest")
    @patch("pilo.commit_manifest_if_changed")
    def test_execute_manifest_update_plan(
        self,
        mock_commit,
        mock_write,
    ):
        cx = pilotest.make_context()

        plan = pilo.build_manifest_update_plan(
            cx,
            ["pile"],
        )

        pilo.execute_manifest_update_plan(cx, plan)

        mock_write.assert_called_once()
        mock_commit.assert_called_once()

    def test_write_manifest(self):
        cx = pilotest.make_context()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            (root / "a.txt").write_text("hello")

            manifest = root / "test.manifest"

            pilo.write_manifest(cx, root, manifest)

            self.assertTrue(manifest.exists())

            text = manifest.read_text()

            self.assertIn("./a.txt", text)

    @patch.object(pilo.Context, "git_commit_if_changed")
    @patch.object(pilo.Context, "ensure_git_repo")
    def test_commit_manifest_if_changed(
        self,
        mock_repo,
        mock_commit,
    ):
        cx = pilotest.make_context()

        manifest = Path("/tmp/test.manifest")

        pilo.commit_manifest_if_changed(
            cx,
            manifest,
            "test update",
        )

        mock_repo.assert_called_once()
        mock_commit.assert_called_once()
