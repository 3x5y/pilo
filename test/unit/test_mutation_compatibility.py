import unittest
from pathlib import Path

from pilo import mutation
from pilo import mutation_events
from pilo import mutation_exec
from pilo import mutation_types
from pilo import mutation_preview
from pilo import mutation_render
import pilotest


class TestManifestCompat(pilotest.TestCase):

    def test_move_mutation_compatibility_alias(self):
        mut = mutation.MoveMutation(
            src=Path("/src"),
            dst=Path("/dst"),
            dataset="tank/pile",
        )

        self.assertIsInstance(mut, mutation_types.MoveMutation)

    def test_operation_event_compatibility_alias(self):
        ev = mutation.OperationEvent(
            kind="move",
            src=Path("/src"),
            dst=Path("/dst"),
            dataset="tank/pile",
        )

        self.assertIsInstance(ev, mutation_events.OperationEvent)

    def test_execute_semantic_mutations_compatibility(self):

        self.assertIs(
            mutation.execute_fs_mutations,
            mutation_exec.execute_fs_mutations,
        )


    def test_execute_mutation_dispatches_by_type(self):

        with pilotest.make_tmp_context() as cx:

            src = cx.path / "src.txt"
            dst = cx.path / "dst.txt"

            src.write_text("hello")

            mut = mutation.MoveMutation(
                src=src,
                dst=dst,
                dataset="tank/pile",
            )

            class DummyExecutor(mutation_exec.MutationExecutor):

                def __init__(self):
                    self.seen = []

                def apply(self, mut):
                    self.seen.append(mut)

            ex = DummyExecutor()

            mutation_exec.apply_mutations(ex, [mut])
            self.assertEqual(ex.seen, [mut])

    def test_preview_execution_compatibility(self):

        self.assertIs(
            mutation.get_preview_events,
            mutation_preview.get_preview_events,
        )


    def test_render_mutation_compatibility(self):

        self.assertIs(
            mutation.render_mutation,
            mutation_render.render_mutation,
        )
