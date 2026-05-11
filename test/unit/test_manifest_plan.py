import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo import context
from pilo import manifest
from pilo import mutation
from pilo.front import ingest
import pilotest


class TestManifestPlan(unittest.TestCase):

    def test_manifest_subset_root(self):
        cx = pilotest.make_context()

        self.assertEqual(
            manifest.manifest_subset_root(cx, "pile"),
            cx.pile_path,
        )

        self.assertEqual(
            manifest.manifest_subset_root(cx, "collection"),
            cx.static_path / "collection",
        )

        self.assertEqual(
            manifest.manifest_subset_root(cx, "filing"),
            cx.static_path / "filing",
        )

    def test_build_manifest_update_plan(self):
        cx = pilotest.make_context()

        plan = manifest.build_manifest_update_plan(
            cx,
            ["pile", "collection"],
        )

        self.assertEqual(
            [s.name for s in plan.subsets],
            ["pile", "collection"]
        )

    @patch("pilo.manifest.write_manifest")
    @patch("pilo.manifest.commit_manifest_if_changed")
    @patch("pilo.fs.ensure_parent_dir")
    def test_execute_manifest_update_plan(
        self,
        mock_dir,
        mock_commit,
        mock_write,
    ):
        cx = pilotest.make_context()

        plan = manifest.build_manifest_update_plan(
            cx,
            ["pile"],
        )

        manifest.execute_manifest_update_plan(cx, plan)

        mock_write.assert_called_once()
        mock_commit.assert_called_once()

    def test_write_manifest(self):
        cx = pilotest.make_context()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            (root / "a.txt").write_text("hello")

            mfile = root / "test.manifest"

            manifest.write_manifest(cx, root, mfile)

            self.assertTrue(mfile.exists())

            text = mfile.read_text()

            self.assertIn("./a.txt", text)

    @patch("pilo.git.commit_if_changed")
    @patch("pilo.git.ensure_repo")
    def test_commit_manifest_if_changed(
        self,
        mock_repo,
        mock_commit,
    ):
        cx = pilotest.make_context()

        mfile = Path("/tmp/test.manifest")

        manifest.commit_manifest_if_changed(
            cx,
            mfile,
            "test update",
        )

        mock_repo.assert_called_once()
        mock_commit.assert_called_once()

    def test_mutation_manifest_domains_for_pile(self):
        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            )
        ]

        doms = mutation.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"pile"})

    def test_mutation_manifest_domains_for_collection(self):
        muts = [
            mutation.SemanticMutation(
                action="copy",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/static/collection",
            )
        ]

        doms = mutation.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"collection"})

    def test_mutation_manifest_domains_for_filing(self):
        muts = [
            mutation.SemanticMutation(
                action="copy",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/static/filing/docs",
            )
        ]

        doms = mutation.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"filing"})

    def test_mutation_manifest_domains_deduplicates(self):
        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.SemanticMutation(
                action="unlink",
                src=Path("/tmp/c"),
                dst=None,
                dataset="tank/a/pile",
            ),
        ]

        doms = mutation.mutation_manifest_domains(muts)

        self.assertEqual(doms, {"pile"})

    def test_build_manifest_plan_for_mutations(self):
        cx = pilotest.make_context()

        muts = [
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static/collection",
            ),
        ]

        plan = mutation.build_manifest_plan_for_mutations(cx, muts)

        names = [u.name for u in plan.subsets]

        self.assertEqual(
            sorted(names),
            ["collection", "pile"],
        )

    @patch("pilo.manifest.write_manifest_entries")
    @patch("pilo.manifest.load_manifest_entries")
    def test_execute_manifest_mutations(
        self,
        mock_load,
        mock_write,
    ):
        cx = pilotest.make_context()

        manifest_path = (
            cx.admin_path /
            "manifest/pile.manifest"
        )

        mock_load.return_value = [
            manifest.ManifestEntry(
                checksum="old",
                path=Path("in/old.txt"),
            )
        ]

        muts = [
            manifest.ManifestAddEntry(
                subset="pile",
                entry=manifest.ManifestEntry(
                    checksum="new",
                    path=Path("in/new.txt"),
                )
            )
        ]

        manifest.execute_manifest_mutations(
            cx,
            "pile",
            manifest_path,
            muts,
        )

        args = mock_write.call_args[0]

        written = args[2]

        self.assertEqual(len(written), 2)

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_ingest_manifest_mutations_move(self, _):

        op = ingest.IngestOp(
            src=Path("/tmp/intake/a.txt"),
            dst=Path("/pile/in/a.txt"),
            dataset="tank/pile",
            action="move",
        )

        muts = ingest.ingest_manifest_mutations(
            [op],
            Path("/pile"),
        )

        self.assertEqual(len(muts), 1)

        mut = muts[0]

        self.assertEqual(mut.subset, "pile")

        self.assertEqual(
            mut.entry.path,
            Path("in/a.txt"),
        )

    def test_ingest_manifest_mutations_noop(self):

        op = ingest.IngestOp(
            src=Path("/tmp/intake/a.txt"),
            dst=Path("/pile/in/a.txt"),
            dataset="tank/pile",
            action="noop",
        )

        muts = ingest.ingest_manifest_mutations(
            [op],
            Path("/pile"),
        )

        self.assertEqual(muts, [])
