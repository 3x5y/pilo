import unittest
from pathlib import Path

from pilo.front import mutation
import pilotest


class TestOperationEvents(pilotest.TestCase):

    def test_move_event(self):
        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        ev = mutation.event_for_mutation(mut)

        self.assertEqual(ev.kind, "move")
        self.assertEqual(ev.src, Path("/tmp/a"))
        self.assertEqual(ev.dst, Path("/tmp/b"))
        self.assertEqual(ev.dataset, "tank/a")

    def test_unlink_event(self):
        mut = mutation.UnlinkMutation(
            path=Path("/tmp/a"),
            dataset="tank/a",
        )

        ev = mutation.event_for_mutation(mut)

        self.assertEqual(ev.kind, "unlink")
        self.assertEqual(ev.src, Path("/tmp/a"))
        self.assertEqual(ev.dst, None)

    def test_render_event(self):
        ev = mutation.OperationEvent(
            kind="move",
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        rendered = mutation.render_event(ev)

        self.assertEqual(
            rendered,
            "move /tmp/a -> /tmp/b",
        )
