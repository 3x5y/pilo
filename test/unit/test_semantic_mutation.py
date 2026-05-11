import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo import mutation
from pilo import mutation_exec
import pilotest


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
    def test_exec_move_mutation(self, mock_move):
        cx = pilotest.make_context()

        mut = mutation.MoveMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/pile",
        )

        mutation_exec.execute_mutation(cx, mut)

        mock_move.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.fs.safe_unlink")
    def test_exec_unlink_mutation(self, mock_unlink):
        cx = pilotest.make_context()

        src = Path("/tmp/a")

        mut = mutation.UnlinkMutation(
            path=src,
            dataset="tank/a/pile",
        )

        mutation_exec.execute_mutation(cx, mut)

        mock_unlink.assert_called_once()

    @patch("pilo.fs.safe_copy")
    def test_exec_copy_mutation(self, mock_copy):
        cx = pilotest.make_context()

        mut = mutation.CopyMutation(
            src=Path("/tmp/a"),
            dst=Path("/tmp/b"),
            dataset="tank/a/static",
        )

        mutation_exec.execute_mutation(cx, mut)

        mock_copy.assert_called_once_with(
            cx,
            Path("/tmp/a"),
            Path("/tmp/b"),
        )

    @patch("pilo.zfs.writable_datasets")
    @patch("pilo.mutation_exec.execute_mutation")
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
            mutation.MoveMutation(
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.CopyMutation(
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
            applied.append(mut)

        muts = [
            mutation.MoveMutation(
                src=Path("/tmp/a"),
                dst=Path("/tmp/b"),
                dataset="tank/a/pile",
            ),
            mutation.CopyMutation(
                src=Path("/tmp/c"),
                dst=Path("/tmp/d"),
                dataset="tank/a/static",
            ),
            mutation.UnlinkMutation(
                path=Path("/tmp/e"),
                dataset="tank/a/pile",
            ),
        ]

        with patch("pilo.mutation_exec.execute_mutation", side_effect=fake_apply):
            with patch("pilo.zfs.writable_datasets") as mock_writable:
                cm = MagicMock()
                cm.__enter__.return_value = None
                cm.__exit__.return_value = None
                mock_writable.return_value = cm
                mutation.execute_semantic_mutations(cx, muts)

        self.assertEqual(applied, muts)

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
            mutation.MoveMutation(
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
                "pilo.mutation_exec.execute_mutation",
                side_effect=fake_apply,
            ):
                mutation.execute_semantic_mutations(cx, muts)

        self.assertEqual(
            events,
            ["enter", "apply", "exit"]
        )


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

        with pilotest.assert_fatal(self):
            mutation.render_mutation(mut)
