import unittest
from pathlib import Path

from pilo import mutation
from pilo.front import ingest
from pilo.front import promote
from pilo.front import prune


class TestExecutionPreview(unittest.TestCase):

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

        rendered = ingest.preview_ingest_plan(plan)

        self.assertEqual(rendered, ["move /tmp/in/a -> /tmp/pile/in/a"])

    def test_preview_promote_plan(self):
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

        rendered = promote.preview_promote_plan(plan)

        self.assertEqual(rendered, ["unlink /tmp/a"])

    def test_preview_prune_plan(self):
        plan = prune.PrunePlan(
            ops=[
                prune.PruneOp(
                    path=Path("/tmp/empty"),
                    dataset="tank/a/pile",
                )
            ]
        )

        rendered = prune.preview_prune_plan(plan)

        self.assertEqual(rendered, ["rmdir /tmp/empty"])
