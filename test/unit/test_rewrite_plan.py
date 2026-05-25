import tempfile
import unittest
from unittest.mock import patch, call
from pathlib import Path

from pilo.content import reorg as rewrite
from pilo.content import execution
from pilo.content import manifest
from pilo.front import mutation
from pilo import paths
import pilotest


class TestRewritePlan(pilotest.TestCase):

    def test_build_rewrite_plan(self):
        with pilotest.make_tmp_context() as cx:
            root = cx.pile_path

            src = root / "in/a.txt"
            src.parent.mkdir(parents=True)
            src.write_text("hello")

            ops = [
                rewrite.RewriteOp(
                    kind="mv",
                    src=Path("in/a.txt"),
                    dst=Path("in/b.txt"),
                )
            ]

            plan = rewrite.build_rewrite_plan(cx, ops)

            self.assertEqual(len(plan.ops), 1)

            resolved = plan.ops[0]

            self.assertEqual(
                resolved.src.path,
                root / "in/a.txt"
            )

            self.assertEqual(
                resolved.dst.path,
                root / "in/b.txt"
            )

    @patch("pilo.front.mutation.execute_fs_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        plan = rewrite.RewritePlan(
            ops=[
                rewrite.resolve_rewrite_op(cx, op)
            ]
        )

        rewrite.execute_rewrite_plan(cx, plan)
        mock_exec.assert_called_once()

    def test_rewrite_plan_mutations(self):
        plan = rewrite.RewritePlan(
            ops=[
                rewrite.ResolvedRewriteOp(
                    op=rewrite.RewriteOp(
                        kind="mv",
                        src=Path("in/a"),
                        dst=Path("in/b"),
                    ),
                    src=paths.Resolved(
                        path=Path("/tmp/a"),
                        dataset="tank/a/pile",
                    ),
                    dst=paths.Resolved(
                        path=Path("/tmp/b"),
                        dataset="tank/a/pile",
                    ),
                )
            ]
        )

        muts = rewrite.build_fs_mutations(plan)

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertIsInstance(mut, mutation.MoveMutation)
        self.assertEqual(mut.src, Path("/tmp/a"))
        self.assertEqual(mut.dst, Path("/tmp/b"))
        self.assertEqual(mut.dataset, "tank/a/pile")

    @patch("pilo.front.mutation.execute_fs_mutations")
    def test_execute_uses_executor2(self, mock_exec):
        cx = pilotest.make_context()

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            ),
            src=paths.Resolved(
                path=Path("/tmp/a"),
                dataset="tank/a/pile",
            ),
            dst=paths.Resolved(
                path=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
        )

        plan = rewrite.RewritePlan([op])
        rewrite.execute_rewrite_plan(cx, plan)
        mock_exec.assert_called_once()

    @patch("pilo.content.checksum.verify_checksum")
    @patch("pilo.checks.require_file")
    def test_rewrite_execution_plan_builds_execution_plan(self, *_):

        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        plan = rewrite.build_rewrite_plan(cx, [op])

        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ]

        exec_plan = rewrite.build_exec_plan(cx, plan, entries)

        self.assertIsInstance(exec_plan, execution.ExecutionPlan)
        self.assertEqual(len(exec_plan.filesystem_steps), 1)
        self.assertEqual(len(exec_plan.manifest_steps), 1)

    @patch("pilo.content.checksum.verify_checksum")
    @patch("pilo.checks.require_file")
    def test_rewrite_execution_plan_contains_manifest_steps(self, *_):

        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        plan = rewrite.build_rewrite_plan(cx, [op])

        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ]

        exec_plan = rewrite.build_exec_plan(cx, plan, entries)

        mop = exec_plan.manifest_steps[0]
        mpath = cx.admin_path / "manifest/pile.manifest"
        self.assertEqual(mop.subset, "pile")
        self.assertEqual(mop.manifest_path, mpath)
        self.assertEqual(len(mop.build_mutations()), 2)


    @patch("pilo.checks.require_file")
    @patch("pilo.content.checksum.verify_checksum")
    def test_rewrite_execution_plan_builds_checksum_verification(self, *_):

        cx = pilotest.make_context()
        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )
        plan = rewrite.build_rewrite_plan(cx, [op])
        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ]
        exec_plan = rewrite.build_exec_plan(
            cx,
            plan,
            entries,
        )

        self.assertEqual(len(exec_plan.preflight_steps), 1)
        step = exec_plan.preflight_steps[0]
        self.assertIsInstance(step, execution.VerifyChecksumStep)
        self.assertEqual(step.expected_checksum, "abc123")

    def test_rewrite_manifest_mutations_use_verified_checksums(self):

        cx = pilotest.make_context()

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )
        verified = {
            Path("in/a.txt"):
                manifest.ProvenancedChecksum(
                    path=Path("in/a.txt"),
                    checksum="abc123",
                    provenance=(
                        manifest.ChecksumProvenance.VERIFIED
                    ),
                )
        }
        muts = rewrite.build_manifest_mutations(
            [op],
            cx.pile_path,
            verified,
        )

        add = muts[1]
        self.assertEqual(add.entry.checksum, "abc123")

    @patch("pilo.content.checksum.verify_checksum")
    def test_rewrite_verified_checksums_reuses_manifest_entries(
        self,
        mock_verify,
    ):

        cx = pilotest.make_context()
        mock_verify.return_value = (
            manifest.ProvenancedChecksum(
                path=Path("in/a.txt"),
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        )

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )

        entries = manifest.ManifestIndex([
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ])

        verified = rewrite.build_checksum_index(
            [op],
            cx.pile_path,
            entries,
        )

        item = verified.require(Path("in/a.txt"))
        self.assertEqual(item.checksum, "abc123")
        mock_verify.assert_called_once_with(
            cx.resolve(Path("in/a.txt")).path,
            "abc123",
        )

    def test_rewrite_verified_checksums_missing_entry_fails(self):

        cx = pilotest.make_context()
        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )
        entries = manifest.ManifestIndex([])

        with pilotest.assert_fatal(self):
            rewrite.build_checksum_index([op], cx.pile_path, entries)

    @patch("pilo.content.checksum.verify_checksum")
    @patch("pilo.checks.require_file")
    @patch("pilo.content.reorg.build_manifest_mutations")
    def test_rewrite_execution_plan_uses_verified_checksums(
        self,
        mock_manifest,
        *_
    ):

        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        plan = rewrite.build_rewrite_plan(cx, [op])

        entries = [
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ]

        exec_plan = rewrite.build_exec_plan(cx, plan, entries)
        exec_plan.manifest_steps[0].build_mutations()
        verified = mock_manifest.call_args[0][2]

        self.assertIsInstance(verified, manifest.ChecksumIndex)

    @patch("pilo.fs.sha256_file")
    def test_rewrite_manifest_mutations_do_not_rehash(
        self,
        mock_sha,
    ):

        verified = (
            manifest.ChecksumIndex([
                manifest.ProvenancedChecksum(
                    path=Path("in/old.txt"),
                    checksum="existing",
                    provenance=(
                        manifest.ChecksumProvenance.VERIFIED
                    ),
                )
            ])
        )
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
        rewrite.build_manifest_mutations(
            [op],
            Path("/pile"),
            verified,
        )

        mock_sha.assert_not_called()

    @patch("pilo.content.checksum.verify_checksum")
    def test_rewrite_verified_checksums_mark_verified(self, mock_verify):

        mock_verify.return_value = manifest.ProvenancedChecksum(
            path=Path("in/a.txt"),
            checksum="abc123",
            provenance=(
                manifest
                .ChecksumProvenance
                .VERIFIED
            ),
        )

        cx = pilotest.make_context()

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )

        entries = manifest.ManifestIndex([
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ])

        verified = rewrite.build_checksum_index(
            [op],
            cx.pile_path,
            entries,
        )

        item = verified.require(Path("in/a.txt"))

        self.assertEqual(item.provenance,
                         manifest.ChecksumProvenance.VERIFIED)

    @patch("pilo.content.checksum.verify_checksum")
    def test_rewrite_verified_checksums_use_acquisition_layer(
        self,
        mock_verify,
    ):

        cx = pilotest.make_context()

        mock_verify.return_value = (
            manifest.ProvenancedChecksum(
                path=Path("in/a.txt"),
                checksum="abc123",
                provenance=(
                    manifest
                    .ChecksumProvenance
                    .VERIFIED
                ),
            )
        )

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )

        entries = manifest.ManifestIndex([
            manifest.ManifestEntry(
                checksum="abc123",
                path=Path("in/a.txt"),
            )
        ])

        rewrite.build_checksum_index(
            [op],
            cx.pile_path,
            entries,
        )

        mock_verify.assert_called_once()

    @patch("pilo.content.continuity.build_mutations")
    @patch("pilo.content.continuity.build_transfers")
    def test_rewrite_manifest_mutations_use_continuity_layer(
        self,
        mock_build,
        mock_manifest,
    ):

        cx = pilotest.make_context()

        op = rewrite.ResolvedRewriteOp(
            op=rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            ),
            src=cx.resolve(Path("in/a.txt")),
            dst=cx.resolve(Path("in/b.txt")),
        )

        rewrite.build_manifest_mutations(
            [op],
            cx.pile_path,
            [],
        )

        mock_build.assert_called_once()
        mock_manifest.assert_called_once()
