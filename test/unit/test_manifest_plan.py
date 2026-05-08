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
    @patch("pilo.ensure_parent_dir")
    def test_execute_manifest_update_plan(
        self,
        mock_dir,
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

    def test_mutation_manifest_domains_for_pile(self):
        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            )
        ]

        doms = pilo.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"pile"})

    def test_mutation_manifest_domains_for_collection(self):
        muts = [
            pilo.SemanticMutation(
                action="copy",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/static/collection",
            )
        ]

        doms = pilo.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"collection"})

    def test_mutation_manifest_domains_for_filing(self):
        muts = [
            pilo.SemanticMutation(
                action="copy",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/static/filing/docs",
            )
        ]

        doms = pilo.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"filing"})

    def test_mutation_manifest_domains_deduplicates(self):
        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            pilo.SemanticMutation(
                action="unlink",
                src=Path("/tmp/c"),
                dst=None,
                dataset="tank/a/pile",
            ),
        ]

        doms = pilo.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"pile"})

    def test_build_manifest_plan_for_mutations(self):
        cx = pilotest.make_context()

        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            pilo.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static/collection",
            ),
        ]

        plan = pilo.build_manifest_plan_for_mutations(
            cx,
            muts,
        )

        names = [u.name for u in plan.subsets]

        self.assertEqual(
            sorted(names),
            ["collection", "pile"],
        )
