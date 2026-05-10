import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo import mutation
import pilotest


class TestSemanticMutation(unittest.TestCase):

    def test_semantic_mutation_model(self):
        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/pile",
        )

        self.assertEqual(mut.src, Path("/tmp/a"))
        self.assertEqual(mut.dst, Path("/tmp/b"))
        self.assertEqual(mut.dataset, "tank/a/pile")

    @patch("pilo.fs.safe_move")
    def test_apply_move_mutation(self, mock_move):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/pile",
        )

        mutation.apply_semantic_mutation(cx, mut)

        mock_move.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.fs.safe_unlink")
    def test_apply_unlink_mutation(self, mock_unlink):
        cx = pilotest.make_context()

        src = Path("/tmp/a")

        mut = mutation.UnlinkMutation(
            path=src,
            dataset="tank/a/pile",
        )

        mutation.apply_semantic_mutation(cx, mut)

        mock_unlink.assert_called_once()

    @patch("pilo.fs.safe_copy")
    def test_apply_copy_mutation(self, mock_copy):
        cx = pilotest.make_context()

        mut = mutation.CopyMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/static",
        )

        mutation.apply_semantic_mutation(cx, mut)

        mock_copy.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.zfs.writable_datasets")
    @patch("pilo.mutation.apply_semantic_mutation")
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
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static",
            ),
        ]

        mutation.execute_semantic_mutations(cx, muts)

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
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.SemanticMutation(
                action="copy",
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static",
            ),
            mutation.SemanticMutation(
                action="unlink",
                src=Path("/tmp/e"),
                dst=None,
                dataset="tank/a/pile",
            ),
        ]

        with patch("pilo.mutation.apply_semantic_mutation", side_effect=fake_apply):
            with patch("pilo.zfs.writable_datasets") as mock_writable:

                cm = MagicMock()
                cm.__enter__.return_value = None
                cm.__exit__.return_value = None

                mock_writable.return_value = cm

                mutation.execute_semantic_mutations(cx, muts)

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
            mutation.SemanticMutation(
                action="move",
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            )
        ]

        with patch(
            "pilo.zfs.writable_datasets",
            return_value=FakeContext(),
        ):
            with patch(
                "pilo.mutation.apply_semantic_mutation",
                side_effect=fake_apply,
            ):
                mutation.execute_semantic_mutations(cx, muts)

        self.assertEqual(
            events,
            ["enter", "apply", "exit"]
        )


class TestMutationDispatch(unittest.TestCase):

    @patch("pilo.fs.safe_move")
    def test_move_dispatch(self, move):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/src"),
            dst=Path("/dst"),
            dataset="tank/a",
        )

        mutation.apply_semantic_mutation(cx, mut)

        move.assert_called_once_with(
            cx,
            Path("/src"),
            Path("/dst"),
        )

    @patch("pilo.fs.safe_copy")
    def test_copy_dispatch(self, copy):
        cx = pilotest.make_context()

        mut = mutation.CopyMutation(
            src=Path("/src"),
            dst=Path("/dst"),
            dataset="tank/a",
        )

        mutation.apply_semantic_mutation(cx, mut)

        copy.assert_called_once_with(
            cx,
            Path("/src"),
            Path("/dst"),
        )

    def test_unknown_action_fails(self):
        cx = pilotest.make_context()

        mut = mutation.SemanticMutation(
            action="invalid",
            src=None,
            dst=None,
            dataset="tank/a",
        )

        with pilotest.assert_fatal(self):
            mutation.apply_semantic_mutation(cx, mut)


class TestMutationTypes(unittest.TestCase):

    def test_move_mutation(self):
        m = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        self.assertEqual(m.src, Path("/tmp/a"))
        self.assertEqual(m.dst, Path("/tmp/b"))
        self.assertEqual(m.dataset, "tank/a")

    def test_copy_mutation(self):
        m = mutation.CopyMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a",
        )

        self.assertEqual(m.src, Path("/tmp/a"))
        self.assertEqual(m.dst, Path("/tmp/b"))

    def test_unlink_mutation(self):
        m = mutation.UnlinkMutation(
            path=Path("/tmp/a"),
            dataset="tank/a",
        )

        self.assertEqual(m.path, Path("/tmp/a"))

    def test_rmdir_mutation(self):
        m = mutation.RmdirMutation(
            path=Path("/tmp/a"),
            dataset="tank/a",
        )

        self.assertEqual(m.path, Path("/tmp/a"))


class TestMutationRender(unittest.TestCase):

    def test_render_move(self):
        mut = mutation.MoveMutation(
            src=Path("/src"),
            dst=Path("/dst"),
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "move /src -> /dst",
        )

    def test_render_copy(self):
        mut = mutation.CopyMutation(
            src=Path("/a"),
            dst=Path("/b"),
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "copy /a -> /b",
        )

    def test_render_unlink(self):
        mut = mutation.UnlinkMutation(
            path=Path("/tmp/a"),
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "unlink /tmp/a",
        )

    def test_render_rmdir(self):
        mut = mutation.RmdirMutation(
            path=Path("/tmp/dir"),
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "rmdir /tmp/dir",
        )

    def test_render_multiple(self):
        muts = [
            mutation.UnlinkMutation(
                path=Path("/a"),
                dataset="tank/a",
            ),
            mutation.RmdirMutation(
                path=Path("/b"),
                dataset="tank/a",
            ),
        ]

        result = mutation.render_mutations(muts)

        self.assertEqual(
            result,
            [
                "unlink /a",
                "rmdir /b",
            ],
        )

    def test_render_unknown_action_fails(self):
        mut = mutation.SemanticMutation(
            action="invalid",
            src=None,
            dst=None,
            dataset="tank/a",
        )

        #with self.assertRaises(AttributeError):
        with pilotest.assert_fatal(self):
            mutation.render_mutation(mut)
