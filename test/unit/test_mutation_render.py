import unittest
from pathlib import Path

from pilo import mutation


class TestMutationRender(unittest.TestCase):

    def test_render_move(self):
        mut = mutation.SemanticMutation(
            action="move",
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
        mut = mutation.SemanticMutation(
            action="copy",
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
        mut = mutation.SemanticMutation(
            action="unlink",
            src=Path("/tmp/a"),
            dst=None,
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "unlink /tmp/a",
        )

    def test_render_rmdir(self):
        mut = mutation.SemanticMutation(
            action="rmdir",
            src=Path("/tmp/dir"),
            dst=None,
            dataset="tank/a",
        )

        result = mutation.render_mutation(mut)

        self.assertEqual(
            result,
            "rmdir /tmp/dir",
        )

    def test_render_multiple(self):
        muts = [
            mutation.SemanticMutation(
                action="unlink",
                src=Path("/a"),
                dst=None,
                dataset="tank/a",
            ),
            mutation.SemanticMutation(
                action="rmdir",
                src=Path("/b"),
                dst=None,
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

        with self.assertRaises(AttributeError):
            mutation.render_mutation(mut)
