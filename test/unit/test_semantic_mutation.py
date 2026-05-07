import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

import pilo
import pilotest


class TestSemanticMutation(unittest.TestCase):

    def test_semantic_mutation_model(self):
        mut = pilo.SemanticMutation(
            action="move",
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/pile",
        )

        self.assertEqual(mut.action, "move")
        self.assertEqual(mut.src, Path("/tmp/a"))
        self.assertEqual(mut.dst, Path("/tmp/b"))
        self.assertEqual(mut.dataset, "tank/a/pile")

    @patch("pilo.safe_move")
    def test_apply_move_mutation(self, mock_move):
        cx = pilotest.make_context()

        mut = pilo.SemanticMutation(
            action="move",
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/pile",
        )

        pilo.apply_semantic_mutation(cx, mut)

        mock_move.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.safe_unlink")
    def test_apply_unlink_mutation(self, mock_unlink):
        cx = pilotest.make_context()

        src = Path("/tmp/a")

        mut = pilo.SemanticMutation(
            action="unlink",
            src=src,
            dst=None,
            dataset="tank/a/pile",
        )

        pilo.apply_semantic_mutation(cx, mut)

        mock_unlink.assert_called_once()

    @patch("pilo.safe_copy")
    def test_apply_copy_mutation(self, mock_copy):
        cx = pilotest.make_context()

        mut = pilo.SemanticMutation(
            action="copy",
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/static",
        )

        pilo.apply_semantic_mutation(cx, mut)

        mock_copy.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.writable_datasets")
    @patch("pilo.apply_semantic_mutation")
    def test_execute_semantic_mutations(
        self,
        mock_apply,
        mock_writable,
    ):
        cx = pilotest.make_context()

        cm = MagicMock()
        cm.__enter__.return_value = None
        mock_writable.return_value = cm

        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            pilo.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static",
            ),
        ]

        pilo.execute_semantic_mutations(cx, muts)

        mock_writable.assert_called_once_with(
            {"tank/a/pile", "tank/a/static"}
        )

        self.assertEqual(mock_apply.call_count, 2)

    def test_execute_applies_all(self):
        cx = pilotest.make_context()

        applied = []

        def fake_apply(_cx, mut):
            applied.append(mut.action)

        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            pilo.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static",
            ),
            pilo.SemanticMutation(
                action="unlink",
                src=Path("/tmp/e"),
                dst=None,
                dataset="tank/a/pile",
            ),
        ]

        with patch("pilo.apply_semantic_mutation", side_effect=fake_apply):
            with patch("pilo.writable_datasets") as mock_writable:

                cm = MagicMock()
                cm.__enter__.return_value = None
                cm.__exit__.return_value = None

                mock_writable.return_value = cm

                pilo.execute_semantic_mutations(cx, muts)

        self.assertEqual(
            applied,
            ["move", "copy", "unlink"]
        )

    def test_execute_wraps_apply_phase(self):
        cx = pilotest.make_context()

        events = []

        class FakeContext:
            def __enter__(self):
                events.append("enter")

            def __exit__(self, exc_type, exc, tb):
                events.append("exit")

        def fake_apply(_cx, _mut):
            events.append("apply")

        muts = [
            pilo.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            )
        ]

        with patch(
            "pilo.writable_datasets",
            return_value=FakeContext(),
        ):
            with patch(
                "pilo.apply_semantic_mutation",
                side_effect=fake_apply,
            ):
                pilo.execute_semantic_mutations(cx, muts)

        self.assertEqual(
            events,
            ["enter", "apply", "exit"]
        )
