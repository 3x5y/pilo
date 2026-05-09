import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pilo import mutation
from pilo.front import prune
import pilotest


class TestPrunePlan(unittest.TestCase):

    def test_prune_op_model(self):
        op = prune.PruneOp(
            path=Path("/tmp/pile/in/a"),
            dataset="tank/a/pile",
        )

        self.assertEqual(
            op.path,
            Path("/tmp/pile/in/a"),
        )

        self.assertEqual(
            op.dataset,
            "tank/a/pile",
        )

    def test_build_prune_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            keep = root / "in"
            keep.mkdir()

            empty = root / "x/y/z"
            empty.mkdir(parents=True)

            nonempty = root / "data"
            nonempty.mkdir()

            (nonempty / "file.txt").write_text("x")

            plan = prune.build_prune_plan(
                root,
                "tank/a/pile",
            )

            paths = [op.path for op in plan.ops]

            self.assertIn(root / "x/y/z", paths)
            self.assertIn(root / "x/y", paths)
            self.assertIn(root / "x", paths)

            self.assertNotIn(root / "in", paths)
            self.assertNotIn(root / "data", paths)

    def test_prune_mutations(self):
        plan = prune.PrunePlan(
            ops = [
                prune.PruneOp(
                    path=Path("/tmp/pile/x"),
                    dataset="tank/a/pile",
                )
            ]
        )

        muts = prune.prune_mutations(plan)

        self.assertEqual(len(muts), 1)
        self.assertEqual(muts[0].action, "rmdir")
        self.assertEqual(muts[0].src, Path("/tmp/pile/x"))

    @patch("pilo.fs.safe_rmdir")
    def test_apply_rmdir_mutation(self, mock_rmdir):
        cx = pilotest.make_context()
        mut = mutation.SemanticMutation(
            action="rmdir",
            src=Path("/tmp/x"),
            dst=None,
            dataset="tank/a/pile",
        )

        mutation.apply_semantic_mutation(cx, mut)

        mock_rmdir.assert_called_once()

    @patch("pilo.mutation.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()
        plan = prune.PrunePlan(
            ops = [
                prune.PruneOp(
                    path=Path("/tmp/pile/x"),
                    dataset="tank/a/pile",
                )
            ]
        )

        prune.execute_prune_plan(cx, plan)

        mock_exec.assert_called_once()
