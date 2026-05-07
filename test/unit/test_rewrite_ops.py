import tempfile
import unittest
from pathlib import Path

import pilo
import pilotest


class TestRewriteOperationModel(unittest.TestCase):

    def test_parse_move_op(self):
        ops = pilo.parse_rewrite_ops([
            "mv\tin/a.txt\tin/b.txt"
        ])

        self.assertEqual(len(ops), 1)

        op = ops[0]

        self.assertEqual(op.kind, "mv")
        self.assertEqual(op.src, Path("in/a.txt"))
        self.assertEqual(op.dst, Path("in/b.txt"))

    def test_parse_rejects_unknown_op(self):
        with self.assertRaises(SystemExit):
            pilo.parse_rewrite_ops([
                "cp\tin/a\tin/b"
            ])

    def test_parse_rejects_absolute_src(self):
        with self.assertRaises(SystemExit):
            pilo.parse_rewrite_ops([
                "mv\t/etc/passwd\tin/x"
            ])

    def test_parse_rejects_parent_escape(self):
        with self.assertRaises(SystemExit):
            pilo.parse_rewrite_ops([
                "mv\t../x\tin/y"
            ])

    def test_resolve_rewrite_op(self):
        cx = pilotest.make_context()

        op = pilo.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        resolved = pilo.resolve_rewrite_op(cx, op)

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

        op = pilo.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("collection/a.txt"),
        )

        with self.assertRaises(SystemExit):
            pilo.validate_rewrite_op(
                cx,
                pilo.resolve_rewrite_op(cx, op),
            )

    def test_validate_rewrite_ops_rejects_duplicate_src(self):
        cx = pilotest.make_context()

        ops = [
            pilo.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            ),
            pilo.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/c"),
            ),
        ]

        resolved = [
            pilo.resolve_rewrite_op(cx, op)
            for op in ops
        ]

        with self.assertRaises(SystemExit):
            pilo.validate_rewrite_ops(cx, resolved)

    def test_validate_rewrite_ops_rejects_duplicate_dst(self):
        cx = pilotest.make_context()

        ops = [
            pilo.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/x"),
            ),
            pilo.RewriteOp(
                kind="mv",
                src=Path("in/b"),
                dst=Path("in/x"),
            ),
        ]

        resolved = [
            pilo.resolve_rewrite_op(cx, op)
            for op in ops
        ]

        with self.assertRaises(SystemExit):
            pilo.validate_rewrite_ops(cx, resolved)

    def test_validate_rewrite_op_requires_source(self):
        with tempfile.TemporaryDirectory() as td:
            cx = pilotest.make_context()

            cx.pile_path = Path(td)

            op = pilo.RewriteOp(
                kind="mv",
                src=Path("in/missing.txt"),
                dst=Path("in/x.txt"),
            )

            resolved = pilo.resolve_rewrite_op(cx, op)

            with self.assertRaises(SystemExit):
                pilo.validate_rewrite_op(cx, resolved)

    def test_validate_rewrite_op_rejects_conflicting_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            cx = pilotest.make_context()
            cx.pile_path = root

            src = root / "in/src.txt"
            dst = root / "in/dst.txt"

            dst.parent.mkdir(parents=True)

            src.write_text("AAA")
            dst.write_text("BBB")

            op = pilo.RewriteOp(
                kind="mv",
                src=Path("in/src.txt"),
                dst=Path("in/dst.txt"),
            )

            resolved = pilo.resolve_rewrite_op(cx, op)

            with self.assertRaises(SystemExit):
                pilo.validate_rewrite_op(cx, resolved)

    def test_validate_rewrite_op_allows_identical_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            cx = pilotest.make_context()
            cx.pile_path = root

            src = root / "in/src.txt"
            dst = root / "in/dst.txt"

            dst.parent.mkdir(parents=True)

            src.write_text("same")
            dst.write_text("same")

            op = pilo.RewriteOp(
                kind="mv",
                src=Path("in/src.txt"),
                dst=Path("in/dst.txt"),
            )

            resolved = pilo.resolve_rewrite_op(cx, op)

            pilo.validate_rewrite_op(cx, resolved)
