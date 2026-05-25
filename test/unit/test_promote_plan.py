import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo import paths
from pilo.content import execution
from pilo.content import manifest
from pilo.content import promote
from pilo.content import mutation
import pilotest


class TestPromotePlan(pilotest.TestCase):

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

        muts = promote.build_fs_mutations(plan)
        self.assertEqual(len(muts), 2)
        self.assertIsInstance(muts[0], mutation.CopyMutation)
        self.assertIsInstance(muts[1], mutation.UnlinkMutation)

    @patch("pilo.content.mutation.execute_fs_mutations")
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



    def test_promote_manifest_mutations_collection_copy(self):

        op = promote.PromoteOp(
            action="copy",
            src=Path("/pile/out/collection/a.txt"),
            dst=Path("/static/collection/a.txt"),
            dataset="tank/static/collection",
        )
        verified = (
            manifest.ChecksumIndex(
                [
                    manifest.ProvenancedChecksum(
                        path=Path("out/collection/a.txt"),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
            verified,
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
        )
        verified = (
            manifest.ChecksumIndex(
                [
                    manifest.ProvenancedChecksum(
                        path=Path("out/filing/docs/x.pdf"),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
            verified,
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

    def test_promote_manifest_mutations_ignore_unlink(self):

        op = promote.PromoteOp(
            action="unlink",
            src=Path("/pile/out/collection/a.txt"),
            dst=None,
            dataset="tank/pile",
        )
        verified = manifest.ChecksumIndex([])
        muts = promote.build_manifest_mutations(
            [op],
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
            verified,
        )

        self.assertEqual(muts, [])

    def test_promote_manifest_mutations_mixed_operations(self):

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
        verified = (
            manifest.ChecksumIndex(
                [
                    manifest.ProvenancedChecksum(
                        path=Path("out/collection/a.txt"),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )
        muts = promote.build_manifest_mutations(
            ops,
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
            verified,
        )

        self.assertEqual(len(muts), 2)
        self.assertIsInstance(muts[0], manifest.ManifestRemoveEntry)
        self.assertIsInstance(muts[1], manifest.ManifestAddEntry)


    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_promote_builds_execution_plan(self, *_):

        cx = pilotest.make_context()

        src = cx.pile_path / "out/collection/a.txt"

        plan = promote.PromotePlan(
            ops=[
                promote.PromoteOp(
                    action="copy",
                    src=src,
                    dst=Path("/tmp/static/collection/a.txt"),
                    dataset="tank/static/collection",
                ),
                promote.PromoteOp(
                    action="unlink",
                    src=src,
                    dst=None,
                    dataset="tank/pile",
                ),
            ]
        )

        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("out/collection/a.txt"),
            )
        ]

        exec_plan = promote.build_exec_plan(cx, plan, entries)

        self.assertIsInstance(exec_plan, execution.ExecutionPlan)
        self.assertEqual(len(exec_plan.filesystem_steps), 2)
        self.assertEqual(len(exec_plan.preflight_steps), 1)
        self.assertEqual(len(exec_plan.manifest_steps), 3)

    def test_promote_preflight_steps_verify_copy_sources(self):

        cx = pilotest.make_context()
        src = cx.pile_path / "out/collection/a.txt"
        ops = [
            promote.PromoteOp(
                action="copy",
                src=src,
                dst=Path("/tmp/static/collection/a.txt"),
                dataset="tank/static/collection",
            ),
            promote.PromoteOp(
                action="unlink",
                src=src,
                dst=None,
                dataset="tank/pile",
            ),
        ]
        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("out/collection/a.txt"),
            )
        ]
        steps = promote.build_preflight_steps(
            ops,
            cx.pile_path,
            entries,
        )

        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertIsInstance(step, execution.VerifyChecksumStep)
        self.assertEqual(step.path, src)
        self.assertEqual(step.expected_checksum, "abc123")

    def test_promote_manifest_steps_build_all_subsets(self):
        cx = pilotest.make_context()
        plan = promote.PromotePlan(ops=[])
        entries = []
        verified = manifest.ChecksumIndex([])
        steps = promote.build_manifest_steps(
            cx,
            plan,
            entries,
            verified
        )

        self.assertEqual(len(steps), 3)
        subsets = [step.subset for step in steps]
        self.assertEqual(subsets, ["pile", "collection", "filing"])

    @patch("pilo.content.checksum.verify_checksum")
    def test_promote_verified_checksums_verify_existing_entries(self,
                                                                mock_verify):

        cx = pilotest.make_context()
        src = cx.pile_path / "out/collection/a.txt"
        ops = [
            promote.PromoteOp(
                action="copy",
                src=src,
                dst=Path(
                    "/tmp/static/collection/a.txt"
                ),
                dataset="tank/static/collection",
            )
        ]
        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path(
                    "out/collection/a.txt"
                ),
            )
        ]
        mock_verify.return_value = (
            manifest.ProvenancedChecksum(
                path=src,
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        )
        verified = promote.build_checksum_index(ops, cx.pile_path, entries)
        item = verified.require(Path("out/collection/a.txt"))
        self.assertEqual(item.checksum, "abc123")
        self.assertEqual(
            item.provenance,
            manifest
            .ChecksumProvenance
            .VERIFIED,
        )
        mock_verify.assert_called_once_with(src, "abc123")

    def test_promote_manifest_mutations_reuse_verified_checksum(self):

        verified = (
            manifest.ChecksumIndex(
                [
                    manifest
                    .ProvenancedChecksum(
                        path=Path(
                            "out/collection/a.txt"
                        ),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )
        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path("/pile/out/collection/a.txt"),
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
            )
        ]
        muts = (
            promote.build_manifest_mutations(
                ops,
                Path("/pile"),
                Path("/static/collection"),
                Path("/static/filing"),
                verified,
            )
        )

        self.assertEqual(len(muts), 2)

        remove = muts[0]
        add = muts[1]

        self.assertEqual(
            remove.subset,
            "pile",
        )

        self.assertEqual(
            add.subset,
            "collection",
        )

        self.assertEqual(
            add.entry.checksum,
            "abc123",
        )

    @patch("pilo.fs.sha256_file")
    def test_promote_manifest_mutations_do_not_hash_destination(
        self,
        mock_sha,
    ):

        verified = (
            manifest.ChecksumIndex(
                [
                    manifest
                    .ProvenancedChecksum(
                        path=Path(
                            "out/collection/a.txt"
                        ),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )
        ops = [
            promote.PromoteOp(
                action="copy",
                src=Path("/pile/out/collection/a.txt"),
                dst=Path("/static/collection/a.txt"),
                dataset="tank/static/collection",
            )
        ]
        promote.build_manifest_mutations(
            ops,
            Path("/pile"),
            Path("/static/collection"),
            Path("/static/filing"),
            verified,
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

    def test_promote_manifest_mutations_use_cross_subset_continuity(
        self,
    ):

        verified = (
            manifest.ChecksumIndex(
                [
                    manifest
                    .ProvenancedChecksum(
                        path=Path(
                            "out/collection/a.txt"
                        ),
                        checksum="abc123",
                        provenance=(
                            manifest
                            .ChecksumProvenance
                            .VERIFIED
                        ),
                    )
                ]
            )
        )

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
                verified,
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
