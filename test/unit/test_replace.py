import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

import pilo
import pilotest


class TestReplacePlan(unittest.TestCase):

    @patch("pilo.validation.require_dataset")
    def test_build_replace_plan(self, *_):
        cx = pilotest.make_context()

        src = Path("/tmp/new.txt")

        resolved = pilo.Resolved(
            path=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(cx, "resolve", return_value=resolved):

                plan = pilo.build_replace_plan(
                    cx,
                    src,
                    Path("collection/a.txt"),
                )

        self.assertEqual(len(plan.ops), 1)

        op = plan.ops[0]

        self.assertEqual(op.src, src)
        self.assertEqual(op.dst, resolved)

    def test_replace_requires_source_file(self):
        cx = pilotest.make_context()

        with patch.object(Path, "is_file", return_value=False):
            with pilotest.assert_fatal(self):

                pilo.build_replace_plan(
                    cx,
                    Path("/tmp/nope.txt"),
                    Path("collection/a.txt"),
                )

    def test_replace_requires_existing_target(self):
            cx = pilotest.make_context()

            resolved = pilo.Resolved(
                path=Path("/tmp/static/collection/a.txt"),
                dataset="tank/a/static/collection",
            )

            def is_file():
                return False

            with patch.object(cx, "resolve", return_value=resolved):
                with patch.object(Path, "is_file", side_effect=[True, False]):

                    with pilotest.assert_fatal(self):
                        pilo.build_replace_plan(
                            cx,
                            Path("/tmp/src.txt"),
                            Path("collection/a.txt"),
                        )

    def test_replace_plan_mutations(self):
        plan = pilo.ReplacePlan(
            ops=[
                pilo.ReplaceOp(
                    src=Path("/tmp/src"),
                    dst=pilo.Resolved(
                        path=Path("/tmp/dst"),
                        dataset="tank/a/static/collection",
                    ),
                )
            ]
        )

        muts = pilo.replace_plan_mutations(plan)

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertEqual(mut.action, "copy")
        self.assertEqual(mut.src, Path("/tmp/src"))
        self.assertEqual(mut.dst, Path("/tmp/dst"))
        self.assertEqual(
            mut.dataset,
            "tank/a/static/collection",
        )

    @patch("pilo.build_replace_plan")
    @patch("pilo.execute_replace_plan")
    @patch("pilo.execute_manifest_update_plan")
    def test_replace_command_uses_plan(
        self,
        mock_upd,
        mock_exec,
        mock_build,
    ):
        cx = pilotest.make_context()

        with patch("pilo.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["/tmp/src.txt", "collection/a.txt"],
            ):

                mod = pilotest.import_command("replace")
                mod.main()

        mock_build.assert_called_once()
        mock_exec.assert_called_once()

    @patch("pilo.mutation.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        plan = pilo.ReplacePlan(
            ops=[
                pilo.ReplaceOp(
                    src=Path("/tmp/src.txt"),
                    dst=pilo.Resolved(
                        path=Path("/tmp/static/collection/a.txt"),
                        dataset="tank/a/static/collection",
                    ),
                )
            ]
        )

        pilo.execute_replace_plan(cx, plan)
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]

        self.assertEqual(args[0], cx)

        muts = args[1]
        self.assertEqual(len(muts), 1)

        mut = muts[0]
        self.assertEqual(mut.action, "copy")
        self.assertEqual(mut.src, Path("/tmp/src.txt"))
        self.assertEqual(
            mut.dst,
            Path("/tmp/static/collection/a.txt"),
        )
        self.assertEqual(
            mut.dataset,
            "tank/a/static/collection",
        )
