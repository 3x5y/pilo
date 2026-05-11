import unittest
from pathlib import Path

from pilo import mutation
from pilo import mutation_events
from pilo import mutation_exec
from pilo import mutation_types
import pilotest


class TestManifestCompat(unittest.TestCase):

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
            mutation.execute_semantic_mutations,
            mutation_exec.execute_semantic_mutations,
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

            mutation_exec.execute_mutations(ex, [mut])
            self.assertEqual(ex.seen, [mut])
