import tempfile
import unittest
from unittest.mock import patch, call
from pathlib import Path

from pilo import mutation
from pilo import paths
from pilo.front import rewrite
import pilotest


class TestRewritePlan(unittest.TestCase):

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

    @patch("pilo.mutation.execute_semantic_mutations")
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

        muts = rewrite.rewrite_plan_mutations(plan)

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertIsInstance(mut, mutation.MoveMutation)
        self.assertEqual(mut.src, Path("/tmp/a"))
        self.assertEqual(mut.dst, Path("/tmp/b"))
        self.assertEqual(mut.dataset, "tank/a/pile")

    @patch("pilo.mutation.execute_semantic_mutations")
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

    @patch("pilo.manifest_update.build_manifest_update_plan")
    @patch("pilo.front.rewrite.execute_rewrite_plan")
    @patch("pilo.front.rewrite.build_rewrite_plan")
    def test_rewrite_command_uses_plan(
        self,
        mock_build,
        mock_execute,
        mock_manifest,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["mv\tin/a\tin/b"]
            ):
                mod = pilotest.import_command("rewrite")
                mod.main()

        mock_build.assert_called_once()
        mock_execute.assert_called_once()
        mock_manifest.assert_called_once()
