import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo import mutation
from pilo import paths
from pilo.front import promote
import pilotest


class TestPromotePlan(unittest.TestCase):

    def test_promote_op_model(self):
        op = promote.PromoteOp(
            src=Path("/tmp/pile/out/collection/a.txt"),
            dst=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
            action="copy",
        )

        self.assertEqual(op.action, "copy")
        self.assertEqual(op.dataset, "tank/a/static/collection")

    @patch("pilo.checks.require_dataset")
    @patch("pilo.fs.files_equal", return_value=True)
    def test_build_promote_plan(self, mock_equal, mock_require):
        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        def iter_files():
            yield src

        with patch("pilo.fs.iter_files", return_value=iter_files()):
            with patch.object(Path, "is_dir", return_value=True):
                with patch.object(Path, "iterdir", return_value=[]):
                    plan = promote.build_promote_plan(cx)

        self.assertEqual(len(plan.ops), 2)
        op = plan.ops[0]
        self.assertEqual(op.src, src)
        self.assertEqual(op.dst, Path("/tmp/static/collection/a.txt"))
        self.assertEqual(op.dataset, "tank/a/static/collection")
        op = plan.ops[1]
        self.assertEqual(op.src, src)
        self.assertEqual(op.action, "unlink")
        self.assertEqual(op.dataset, cx.pile_dataset)


    def test_promote_mutations(self):
        plan = promote.PromotePlan(
            ops = [
                promote.PromoteOp(
                    action="copy",
                    src=Path("/tmp/a"),
                    dst=Path("/tmp/static/a"),
                    dataset="tank/a/static/collection",
                ),
                promote.PromoteOp(
                    action="unlink",
                    src=Path("/tmp/a"),
                    dst=None,
                    dataset="tank/a/pile",
                ),
            ]
        )

        muts = promote.promote_plan_mutations(plan)
        self.assertEqual(len(muts), 2)
        self.assertIsInstance(muts[0], mutation.CopyMutation)
        self.assertIsInstance(muts[1], mutation.UnlinkMutation)

    @patch("pilo.mutation.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        plan = promote.PromotePlan(
            ops = [
                promote.PromoteOp(
                    src=cx.pile_path / "out/collection/a.txt",
                    dst=Path("/tmp/static/collection/a.txt"),
                    dataset="tank/a/static/collection",
                    action="copy",
                )
            ]
        )

        promote.execute_promote_plan(cx, plan)
        mock_exec.assert_called_once()

    @patch("pilo.checks.require_dataset")
    @patch("pilo.fs.files_equal", return_value=True)
    def test_existing_identical_file_becomes_noop(
        self,
        mock_equal,
        mock_require,
    ):
        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        resolved = paths.Resolved(
            path=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
        )

        def iter_files():
            yield src

        with patch.object(cx, "resolve", return_value=resolved):
            with patch.object(Path, "is_file", return_value=True):
                with patch("pilo.fs.iter_files", return_value=iter_files()):
                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "iterdir", return_value=[]):
                            plan = promote.build_promote_plan(cx)

        self.assertEqual(plan.ops[0].action, "unlink")



    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_promote_manifest_mutations_collection_copy(self, _):

        op = promote.PromoteOp(
            action="copy",
            src=Path("/pile/out/collection/a.txt"),
            dst=Path("/static/collection/a.txt"),
            dataset="tank/static/collection",
        )

        muts = promote.promote_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 1)

        mut = muts[0]

        self.assertEqual(mut.subset, "collection")

        self.assertEqual(
            mut.entry.path,
            Path("a.txt"),
        )

        self.assertEqual(
            mut.entry.checksum,
            "abc123",
        )

    @patch("pilo.fs.sha256_file", return_value="fff999")
    def test_promote_manifest_mutations_filing_copy(self, _):

        op = promote.PromoteOp(
            action="copy",
            src=Path("/pile/out/filing/docs/x.pdf"),
            dst=Path("/static/filing/docs/x.pdf"),
            dataset="tank/static/filing/docs",
        )

        muts = promote.promote_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 1)

        mut = muts[0]

        self.assertEqual(mut.subset, "filing")

        self.assertEqual(
            mut.entry.path,
            Path("docs/x.pdf"),
        )

    def test_promote_manifest_mutations_unlink_removes_pile_entry(self):

        op = promote.PromoteOp(
            action="unlink",
            src=Path("/pile/out/collection/a.txt"),
            dst=None,
            dataset="tank/pile",
        )

        muts = promote.promote_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 1)

        mut = muts[0]

        self.assertEqual(mut.subset, "pile")

        self.assertEqual(
            mut.path,
            Path("out/collection/a.txt"),
        )

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_promote_manifest_mutations_mixed_operations(self, _):

        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path("/pile/out/collection/a.txt"),
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
            ),

            promote.PromoteOp(
                action="unlink",
                src=Path("/pile/out/collection/a.txt"),
                dst=None,
                dataset="tank/pile",
            ),
        ]

        muts = promote.promote_manifest_mutations(
            ops,
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 2)

        self.assertEqual(
            type(muts[0]).__name__,
            "ManifestAddEntry",
        )

        self.assertEqual(
            type(muts[1]).__name__,
            "ManifestRemoveEntry",
        )
