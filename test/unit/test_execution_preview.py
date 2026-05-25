import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.content import ingest
from pilo.content import prune
from pilo.content import promote
from pilo.content import mutation
import pilotest


class TestExecutionPreview(pilotest.TestCase):

    def test_render_move_mutation(self):
        muts = [
            mutation.MoveMutation(
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a",
            )
        ]

        rendered = mutation.render_mutations(muts)

        self.assertEqual(rendered, ["move /tmp/a -> /tmp/b"])

    def test_render_copy_mutation(self):
        muts = [
            mutation.CopyMutation(
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a",
            )
        ]

        rendered = mutation.render_mutations(muts)

        self.assertEqual(rendered, ["copy /tmp/a -> /tmp/b"])

    def test_render_unlink_mutation(self):
        muts = [
            mutation.UnlinkMutation(
                path=Path("/tmp/a"),
                dataset="tank/a",
            )
        ]

        rendered = mutation.render_mutations(muts)

        self.assertEqual(rendered, ["unlink /tmp/a"])

    def test_render_rmdir_mutation(self):
        muts = [
            mutation.RmdirMutation(
                path=Path("/tmp/a"),
                dataset="tank/a",
            )
        ]

        rendered = mutation.render_mutations(muts)

        self.assertEqual(rendered, ["rmdir /tmp/a"])

    def test_preview_ingest_ops(self):
        cx = pilotest.make_context()
        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=Path("/tmp/in/a"),
                    dst=Path("/tmp/pile/in/a"),
                    dataset="tank/a/pile",
                    action="move",
                )
            ]
        )

        rendered = ingest.preview_ingest_plan(cx, plan)

        self.assertEqual(rendered, ["move /tmp/in/a -> /tmp/pile/in/a"])

    def test_preview_promote_plan(self):
        cx = pilotest.make_context()
        plan = promote.PromotePlan(
            ops=[
                promote.PromoteOp(
                    action="unlink",
                    src=Path("/tmp/a"),
                    dst=None,
                    dataset="tank/a/pile",
                )
            ]
        )

        rendered = promote.preview_promote_plan(cx, plan)

        self.assertEqual(rendered, ["unlink /tmp/a"])

    def test_preview_prune_plan(self):
        cx = pilotest.make_context()
        plan = prune.PrunePlan(
            ops=[
                prune.PruneOp(
                    path=Path("/tmp/empty"),
                    dataset="tank/a/pile",
                )
            ]
        )

        rendered = prune.preview_prune_plan(cx, plan)

        self.assertEqual(rendered, ["rmdir /tmp/empty"])



class TestMutationExecutors(pilotest.TestCase):

    @patch("pilo.fs.safe_move")
    def test_live_executor_moves(self, mock_move):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        ex = mutation.LiveExecutor(cx)

        ex.apply(mut)

        mock_move.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.fs.safe_move")
    def test_preview_executor_does_not_move(self, mock_move):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        ex = mutation.PreviewExecutor(cx)

        ex.apply(mut)

        mock_move.assert_not_called()

    @patch("pilo.zfs.writable_datasets")
    def test_preview_executor_skips_writable_context(
        self,
        mock_writable,
    ):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        mutation.get_preview_events(cx, [mut])

        mock_writable.assert_not_called()

    @patch("pilo.zfs.writable_datasets")
    @patch('pilo.fs.safe_move')
    def test_live_execution_uses_writable_context(
        self,
        mock_move,
        mock_writable,
    ):
        cx = pilotest.make_context()

        mock_writable.return_value.__enter__.return_value = None
        mock_writable.return_value.__exit__.return_value = None

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        mutation.execute_fs_mutations(cx, [mut])

        mock_writable.assert_called_once_with({"tank/a"})
        mock_move.assert_called_once_with(cx, mut.src, mut.dst)

    def test_preview_execution_returns_events(self):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        events = mutation.get_preview_events(cx, [mut])

        self.assertEqual(len(events), 1)

        ev = events[0]

        self.assertEqual(ev.kind, "move")
        self.assertEqual(ev.src, Path("/tmp/a"))
        self.assertEqual(ev.dst, Path("/tmp/b"))
