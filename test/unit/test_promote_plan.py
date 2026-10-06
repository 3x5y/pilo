from contextlib import contextmanager
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo import fs
from pilo import paths
from pilo.content import execution
from pilo.content import manifest
from pilo.content import promote
from pilo.content import mutation
import pilotest


PILE_REL = Path("out/collection/a.txt")


def write_manifest_file(cx, entries):
    path = cx.admin_path / "manifest/pile.manifest"
    path.parent.mkdir(parents=True)
    lines = [
        manifest.render_manifest_entry(
            manifest.ManifestEntry(checksum=checksum, path=rel)
        )
        for checksum, rel in entries
    ]
    path.write_text("".join(line + "\n" for line in lines))
    return path


@contextmanager
def promote_fixture(content="data\n", write_manifest=True):
    """Pile holding one file under out/collection.

    write_manifest writes a pile manifest containing the real checksum
    of the source file; otherwise no manifest is written.
    """
    with pilotest.tmpdir() as td:
        cx = pilotest.make_context(td)
        src = cx.pile_path / PILE_REL
        src.parent.mkdir(parents=True)
        src.write_text(content)
        if write_manifest:
            write_manifest_file(cx, [(fs.hash_file1(src), PILE_REL)])
        yield cx, src


class TestPromotePlan(pilotest.TestCase):

    def test_promote_op_model(self):
        op = promote.PromoteOp(
            src=Path("/tmp/pile/out/collection/a.txt"),
            dst=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
            action="copy",
            checksum="abc123",
        )

        self.assertEqual(op.action, "copy")
        self.assertEqual(op.dataset, "tank/a/static/collection")
        self.assertEqual(op.checksum, "abc123")

    def test_promote_op_model_unlink_has_no_checksum(self):
        op = promote.PromoteOp(
            src=Path("/tmp/pile/out/collection/a.txt"),
            dst=None,
            dataset="tank/a/pile",
            action="unlink",
        )

        self.assertIsNone(op.checksum)

    @patch("pilo.checks.require_dataset")
    def test_build_promote_plan(self, mock_require):
        with promote_fixture() as (cx, src):
            plan = promote.build_promote_plan(cx)

            self.assertEqual(len(plan.ops), 2)

            copy_op = plan.ops[0]
            self.assertEqual(copy_op.action, "copy")
            self.assertEqual(copy_op.src, src)
            self.assertEqual(copy_op.dst, cx.collection_path / "a.txt")
            self.assertEqual(copy_op.dataset, cx.collection_dataset)
            self.assertEqual(copy_op.checksum, fs.hash_file1(src))

            unlink_op = plan.ops[1]
            self.assertEqual(unlink_op.action, "unlink")
            self.assertEqual(unlink_op.src, src)
            self.assertEqual(unlink_op.dataset, cx.pile_dataset)
            self.assertIsNone(unlink_op.checksum)

    @patch("pilo.checks.require_dataset")
    def test_promote_plan_contains_verified_copy_checksums(
        self,
        mock_require,
    ):
        with promote_fixture() as (cx, src):
            expected = fs.hash_file1(src)
            plan = promote.build_promote_plan(cx)

        copy_ops = [op for op in plan.ops if op.action == "copy"]

        self.assertEqual(len(copy_ops), 1)
        self.assertEqual(copy_ops[0].checksum, expected)

    @patch("pilo.checks.require_dataset")
    def test_promote_plan_checksum_mismatch(self, mock_require):
        with promote_fixture(write_manifest=False) as (cx, src):
            write_manifest_file(cx, [("0" * 64, PILE_REL)])
            with self.assert_fatal() as fatal:
                promote.build_promote_plan(cx)

        self.assertIn(
            "checksum verification failed",
            str(fatal.exception),
        )

    @patch("pilo.checks.require_dataset")
    def test_promote_plan_missing_checksum_entry(self, mock_require):
        with promote_fixture(write_manifest=False) as (cx, src):
            with self.assert_fatal() as fatal:
                promote.build_promote_plan(cx)

        self.assertIn("manifest entry missing", str(fatal.exception))

    @patch("pilo.checks.require_dataset")
    def test_promote_conflict_precedes_checksum_lookup(
        self,
        mock_require,
    ):
        # no manifest: a conflict must still be reported as a conflict
        with promote_fixture(write_manifest=False) as (cx, src):
            dst = cx.collection_path / "a.txt"
            dst.parent.mkdir(parents=True)
            dst.write_text("other\n")
            with self.assert_fatal() as fatal:
                promote.build_promote_plan(cx)

        self.assertIn("destination conflict", str(fatal.exception))

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

        muts = promote.build_fs_mutations(plan)
        self.assertEqual(len(muts), 2)
        self.assertIsInstance(muts[0], mutation.CopyMutation)
        self.assertIsInstance(muts[1], mutation.UnlinkMutation)

    @patch("pilo.content.manifest.verify_checksum")
    @patch("pilo.checks.require_dataset")
    @patch("pilo.fs.files_equal", return_value=True)
    def test_existing_identical_file_becomes_noop(
        self,
        mock_equal,
        mock_require,
        mock_verify,
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
        self.assertIsNone(plan.ops[0].checksum)

        # nothing is copied, so nothing is verified
        mock_verify.assert_not_called()

    def test_promote_manifest_mutations_collection_copy(self):

        op = promote.PromoteOp(
            action="copy",
            src=Path("/pile/out/collection/a.txt"),
            dst=Path("/static/collection/a.txt"),
            dataset="tank/static/collection",
            checksum="abc123",
        )
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(remove.subset, "pile")

        self.assertEqual(
            remove.path,
            Path("out/collection/a.txt"),
        )

        self.assertEqual(add.subset, "collection")

        self.assertEqual(
            add.entry.path,
            Path("a.txt"),
        )

        self.assertEqual(
            add.entry.checksum,
            "abc123",
    )

    def test_promote_manifest_mutations_filing_copy(self):

        op = promote.PromoteOp(
            action="copy",
            src=Path("/pile/out/filing/docs/x.pdf"),
            dst=Path("/static/filing/docs/x.pdf"),
            dataset="tank/static/filing/docs",
            checksum="abc123",
        )
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(remove.subset, "pile")

        self.assertEqual(
            remove.path,
            Path("out/filing/docs/x.pdf"),
        )

        self.assertEqual(add.subset, "filing")

        self.assertEqual(
            add.entry.path,
            Path("docs/x.pdf"),
        )

        self.assertEqual(
            add.entry.checksum,
            "abc123",
        )

    def test_promote_manifest_mutations_unlink_only_removes_pile_entry(self):

        op = promote.PromoteOp(
            action="unlink",
            src=Path("/pile/out/collection/a.txt"),
            dst=None,
            dataset="tank/pile",
        )
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 1)

        remove = muts[0]
        self.assertIsInstance(remove, manifest.ManifestRemoveEntry)
        self.assertEqual(remove.subset, "pile")
        self.assertEqual(remove.path, Path("out/collection/a.txt"))

    def test_promote_manifest_mutations_mixed_operations(self):

        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path("/pile/out/collection/a.txt"),
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
                checksum="abc123",
            ),

            promote.PromoteOp(
                action="unlink",
                src=Path("/pile/out/collection/a.txt"),
                dst=None,
                dataset="tank/pile",
            ),
        ]
        muts = promote.build_manifest_mutations(
            ops,
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(muts), 2)
        self.assertIsInstance(muts[0], manifest.ManifestRemoveEntry)
        self.assertIsInstance(muts[1], manifest.ManifestAddEntry)

    @patch("pilo.fs.hash_file1")
    def test_promote_builds_execution_plan(self, mock_sha):

        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        plan = promote.PromotePlan(
            ops=[
                promote.PromoteOp(
                    action="copy",
                    src=src,
                    dst=Path("/tmp/static/collection/a.txt"),
                    dataset="tank/static/collection",
                    checksum="abc123",
                ),
                promote.PromoteOp(
                    action="unlink",
                    src=src,
                    dst=None,
                    dataset="tank/pile",
                ),
            ]
        )

        exec_plan = promote.build_exec_plan(cx, plan)

        self.assertIsInstance(exec_plan, execution.ExecutionPlan)
        self.assertEqual(len(exec_plan.filesystem_steps), 2)
        self.assertEqual(len(exec_plan.manifest_steps), 3)

        # the plan already carries the checksum
        mock_sha.assert_not_called()

    def test_promote_manifest_steps_build_all_subsets(self):
        cx = pilotest.make_context()
        plan = promote.PromotePlan(ops=[])
        steps = promote.build_manifest_steps(cx, plan)

        self.assertEqual(len(steps), 3)
        subsets = [step.subset for step in steps]
        self.assertEqual(subsets, ["pile", "collection", "filing"])

    @patch("pilo.fs.hash_file1")
    def test_promote_manifest_mutations_do_not_hash_destination(
        self,
        mock_sha,
    ):

        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path("/pile/out/collection/a.txt"),
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
                checksum="abc123",
            )
        ]
        promote.build_manifest_mutations(
            ops,
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
        )
        mock_sha.assert_not_called()

    def test_promote_continuity_mappings(self):

        cx = pilotest.make_context()
        ops = [
            promote.PromoteOp(
                action="copy",
                src=cx.pile_path / "out/collection/a.txt",
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
                checksum="abc123",
            )
        ]
        mappings = promote.promote_continuity_mappings(
            ops,
            cx.pile_path,
            Path("/static/collection"),
            Path("/static/filing"),
        )

        self.assertEqual(len(mappings), 1)
        mapping = mappings[0]
        self.assertEqual(mapping.src, Path("out/collection/a.txt"))
        self.assertEqual(mapping.dst, Path("a.txt"))
        self.assertEqual(mapping.checksum, "abc123")

    def test_promote_manifest_mutations_use_cross_subset_continuity(
        self,
    ):

        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path(
                    "/pile/out/collection/a.txt"
                ),
                dst=Path(
                    "/static/collection/a.txt"
                ),
                dataset="tank/static/collection",
                checksum="abc123",
            ),

            promote.PromoteOp(
                action="unlink",
                src=Path(
                    "/pile/out/collection/a.txt"
                ),
                dst=None,
                dataset="tank/pile",
            ),
        ]

        muts = (
            promote.build_manifest_mutations(
                ops,
                Path("/pile"),
                Path("/static/collection"),
                Path("/static/filing"),
            )
        )

        self.assertEqual(len(muts), 2)

        self.assertEqual(
            muts[0].subset,
            "pile",
        )

        self.assertEqual(
            muts[1].subset,
            "collection",
        )