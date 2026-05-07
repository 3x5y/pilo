import tempfile
import unittest
from unittest.mock import patch, call
from pathlib import Path

import pilo
import pilotest


class TestRewritePlan(unittest.TestCase):

    def test_build_rewrite_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            cx = pilotest.make_context()
            cx.pile_path = root

            src = root / "in/a.txt"
            src.parent.mkdir(parents=True)
            src.write_text("hello")

            ops = [
                pilo.RewriteOp(
                    kind="mv",
                    src=Path("in/a.txt"),
                    dst=Path("in/b.txt"),
                )
            ]

            plan = pilo.build_rewrite_plan(cx, ops)

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

    @patch("pilo.zfs.get_readonly", return_value=False)
    def test_apply_rewrite_op_moves_file(self, _):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            cx = pilotest.make_context()
            cx.pile_path = root

            src = root / "in/a.txt"
            dst = root / "in/b.txt"

            src.parent.mkdir(parents=True)

            src.write_text("hello")

            op = pilo.RewriteOp(
                kind="mv",
                src=Path("in/a.txt"),
                dst=Path("in/b.txt"),
            )

            resolved = pilo.resolve_rewrite_op(cx, op)

            pilo.apply_rewrite_op(cx, resolved)

            self.assertFalse(src.exists())
            self.assertEqual(dst.read_text(), "hello")

    @patch("pilo.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        op = pilo.RewriteOp(
            kind="mv",
            src=Path("in/a.txt"),
            dst=Path("in/b.txt"),
        )

        plan = pilo.RewritePlan(
            ops=[
                pilo.resolve_rewrite_op(cx, op)
            ]
        )

        pilo.execute_rewrite_plan(cx, plan)
        mock_exec.assert_called_once()

    @patch("pilo.execute_semantic_mutations")
    def test_execute_uses_executor2(self, mock_exec):
        cx = pilotest.make_context()

        op = pilo.ResolvedRewriteOp(
            op=pilo.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            ),
            src=pilo.Resolved(
                path=Path("/tmp/a"),
                dataset="tank/a/pile",
            ),
            dst=pilo.Resolved(
                path=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
        )

        plan = pilo.RewritePlan([op])
        pilo.execute_rewrite_plan(cx, plan)
        mock_exec.assert_called_once()

    @patch("pilo.run")
    @patch("pilo.execute_rewrite_plan")
    @patch("pilo.build_rewrite_plan")
    def test_rewrite_command_uses_plan(
        self,
        mock_build,
        mock_execute,
        mock_run,
    ):
        cx = pilotest.make_context()

        with patch("pilo.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["mv\tin/a\tin/b"]
            ):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_build.assert_called_once()
        mock_execute.assert_called_once()

    @patch("pilo.safe_move")
    @patch("pilo.dataset_writable")
    def test_apply_rewrite_op_no_longer_opens_context(
        self,
        mock_ctx,
        mock_move,
    ):
        cx = pilotest.make_context()

        op = pilo.ResolvedRewriteOp(
            op=pilo.RewriteOp(
                kind="mv",
                src=Path("in/a"),
                dst=Path("in/b"),
            ),
            src=pilo.Resolved(
                path=Path("/tmp/a"),
                dataset="tank/pile",
            ),
            dst=pilo.Resolved(
                path=Path("/tmp/b"),
                dataset="tank/pile",
            ),
        )

        pilo.apply_rewrite_op(cx, op)

        mock_ctx.assert_not_called()
