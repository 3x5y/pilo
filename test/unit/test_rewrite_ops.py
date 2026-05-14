import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pilo.front import rewrite
import pilotest


class TestRewriteOperationModel(pilotest.TestCase):

    def test_parse_move_op(self):
        ops = rewrite.parse_rewrite_ops([
            "mv\tin/a.txt\tin/b.txt"
        ])

        self.assertEqual(len(ops), 1)

        op = ops[0]

        self.assertEqual(op.kind, "mv")
        self.assertEqual(op.src, Path("in/a.txt"))
        self.assertEqual(op.dst, Path("in/b.txt"))

    def test_parse_rejects_unknown_op(self):
        with pilotest.assert_fatal(self):
            rewrite.parse_rewrite_ops([
                "cp\tin/a\tin/b"
            ])

    def test_parse_rejects_absolute_src(self):
        with pilotest.assert_fatal(self):
            rewrite.parse_rewrite_ops([
                "mv\t/etc/passwd\tin/x"
            ])

    def test_parse_rejects_parent_escape(self):
        with pilotest.assert_fatal(self):
            rewrite.parse_rewrite_ops([
                "mv\t../x\tin/y"
            ])

    def test_resolve_rewrite_op(self):
        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        resolved = rewrite.resolve_rewrite_op(cx, op)

        self.assertEqual(
            resolved.src.path,
            cx.pile_path / "in/a.txt"
        )

        self.assertEqual(
            resolved.dst.path,
            cx.pile_path / "in/b.txt"
        )

    def test_validate_rewrite_op_rejects_cross_domain(self):
        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("collection/a.txt"),
        )

        with pilotest.assert_fatal(self):
            rewrite.validate_rewrite_op(
                cx,
                rewrite.resolve_rewrite_op(cx, op),
            )

    def test_validate_rewrite_ops_rejects_duplicate_src(self):
        cx = pilotest.make_context()

        ops = [
            rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            ),
            rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/c"),
            ),
        ]

        resolved = [
            rewrite.resolve_rewrite_op(cx, op)
            for op in ops
        ]

        with pilotest.assert_fatal(self):
            rewrite.validate_rewrite_ops(cx, resolved)

    def test_validate_rewrite_ops_rejects_duplicate_dst(self):
        cx = pilotest.make_context()

        ops = [
            rewrite.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/x"),
            ),
            rewrite.RewriteOp(
                kind="mv",
                src=Path("in/b"),
                dst=Path("in/x"),
            ),
        ]

        resolved = [
            rewrite.resolve_rewrite_op(cx, op)
            for op in ops
        ]

        with pilotest.assert_fatal(self):
            rewrite.validate_rewrite_ops(cx, resolved)

    def test_validate_rewrite_op_requires_source(self):
        with pilotest.make_tmp_context() as cx:

            op = rewrite.RewriteOp(
                kind="mv",
                src=Path("in/missing.txt"),
                dst=Path("in/x.txt"),
            )

            resolved = rewrite.resolve_rewrite_op(cx, op)

            with pilotest.assert_fatal(self):
                rewrite.validate_rewrite_op(cx, resolved)

    def test_validate_rewrite_op_rejects_conflicting_destination(self):
        with pilotest.make_tmp_context() as cx:
            root = cx.pile_path

            src = root / "in/src.txt"
            dst = root / "in/dst.txt"

            dst.parent.mkdir(parents=True)

            src.write_text("AAA")
            dst.write_text("BBB")

            op = rewrite.RewriteOp(
                kind="mv",
                src=Path("in/src.txt"),
                dst=Path("in/dst.txt"),
            )

            resolved = rewrite.resolve_rewrite_op(cx, op)

            with pilotest.assert_fatal(self):
                rewrite.validate_rewrite_op(cx, resolved)

    def test_validate_rewrite_op_allows_identical_destination(self):
        with pilotest.make_tmp_context() as cx:
            root = cx.pile_path

            src = root / "in/src.txt"
            dst = root / "in/dst.txt"

            dst.parent.mkdir(parents=True)

            src.write_text("same")
            dst.write_text("same")

            op = rewrite.RewriteOp(
                kind="mv",
                src=Path("in/src.txt"),
                dst=Path("in/dst.txt"),
            )

            resolved = rewrite.resolve_rewrite_op(cx, op)

            rewrite.validate_rewrite_op(cx, resolved)

    def test_parse_remove_op(self):

        ops = rewrite.parse_rewrite_ops(["rm\tin/a.txt"])

        self.assertEqual(len(ops), 1)

        op = ops[0]

        self.assertEqual(op.kind, "rm")
        self.assertEqual(op.src, Path("in/a.txt"))
        self.assertIsNone(op.dst)

    def test_parse_remove_op_rejects_extra_fields(self):

        with pilotest.assert_fatal(self):
            rewrite.parse_rewrite_ops(["rm\tin/a.txt\tjunk"])

    def test_validate_remove_op_requires_source(self):

        with pilotest.make_tmp_context() as cx:

            op = rewrite.RewriteOp(
                kind="rm",
                src=Path("in/missing.txt"),
            )

            resolved = rewrite.resolve_rewrite_op(cx, op)

            with pilotest.assert_fatal(self):
                rewrite.validate_rewrite_op(cx, resolved)

    @patch("pilo.checks.require_file")
    def test_build_fs_mutations_remove(self, *_):
        cx = pilotest.make_context()
        op = rewrite.RewriteOp(
            kind="rm",
            src=Path("in/a.txt"),
        )
        plan = rewrite.build_rewrite_plan(cx, [op])
        muts = rewrite.build_fs_mutations(plan)

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertEqual(mut.path, cx.pile_path / "in/a.txt")

    def test_build_manifest_mutations_remove(self):

        cx = pilotest.make_context()

        op = rewrite.RewriteOp(
            kind="rm",
            src=Path("in/a.txt"),
        )

        resolved = rewrite.resolve_rewrite_op(cx, op)

        verified = {}

        muts = rewrite.build_manifest_mutations(
            [resolved],
            cx.pile_path,
            verified,
        )

        self.assertEqual(len(muts), 1)

        mut = muts[0]

        self.assertEqual(mut.subset, "pile")
        self.assertEqual(mut.path, Path("in/a.txt"))

    def test_build_fs_mutations_remove(self):
        with pilotest.make_tmp_context() as cx:

            src = cx.pile_path / "in/a.txt"
            src.parent.mkdir(parents=True)
            src.write_text("AAA")

            op = rewrite.RewriteOp(
                kind="rm",
                src=Path("in/a.txt"),
                dst=None,
            )

            plan = rewrite.build_rewrite_plan(cx, [op])

            muts = rewrite.build_fs_mutations(plan)

            self.assertEqual(len(muts), 1)

            mut = muts[0]

            self.assertEqual(type(mut).__name__, "UnlinkMutation")
            self.assertEqual(mut.path, src)
