import unittest
from pathlib import Path

from pilo import mutation
from pilo import mutation_events
from pilo import mutation_types


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
