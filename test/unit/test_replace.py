import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from pathlib import Path

from pilo.content import replace
from pilo.front import mutation
from pilo import paths
from pilo.front.execution import ExecutionPlan
import pilotest


class TestReplacePlan(pilotest.TestCase):

    @patch("pilo.checks.require_dataset")
    def test_build_replace_plan(self, *_):
        cx = pilotest.make_context()

        src = Path("/tmp/new.txt")

        resolved = paths.Resolved(
            path=Path("/tmp/static/collection/a.txt"),
            dataset="tank/a/static/collection",
        )

        with patch.object(Path, "is_file", return_value=True):
            with patch.object(cx, "resolve", return_value=resolved):

                plan = replace.build_replace_plan(
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

                replace.build_replace_plan(
                    cx,
                    Path("/tmp/nope.txt"),
                    Path("collection/a.txt"),
                )

    def test_replace_requires_existing_target(self):
            cx = pilotest.make_context()

            resolved = paths.Resolved(
                path=Path("/tmp/static/collection/a.txt"),
                dataset="tank/a/static/collection",
            )

            def is_file():
                return False

            with patch.object(cx, "resolve", return_value=resolved):
                with patch.object(Path, "is_file", side_effect=[True, False]):

                    with pilotest.assert_fatal(self):
                        replace.build_replace_plan(
                            cx,
                            Path("/tmp/src.txt"),
                            Path("collection/a.txt"),
                        )

    def test_replace_plan_mutations(self):
        plan = replace.ReplacePlan(
            ops=[
                replace.ReplaceOp(
                    src=Path("/tmp/src"),
                    dst=paths.Resolved(
                        path=Path("/tmp/dst"),
                        dataset="tank/a/static/collection",
                    ),
                )
            ]
        )

        muts = replace.build_fs_mutations(plan)

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertIsInstance(mut, mutation.CopyMutation)
        self.assertEqual(mut.src, Path("/tmp/src"))
        self.assertEqual(mut.dst, Path("/tmp/dst"))
        self.assertEqual(
            mut.dataset,
            "tank/a/static/collection",
        )

    @patch("pilo.front.replace.build_replace_plan")
    @patch("pilo.front.replace.execute_replace_plan")
    @patch("pilo.front.manifest.execute_manifest_update_plan")
    def _test_replace_command_uses_plan(
        self,
        mock_upd,
        mock_exec,
        mock_build,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            with patch.object(
                cx,
                "args",
                ["/tmp/src.txt", "collection/a.txt"],
            ):

                mod = pilotest.import_command("replace")
                mod.main()

        mock_build.assert_called_once()
        mock_exec.assert_called_once()

    @patch("pilo.front.mutation.execute_fs_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        plan = replace.ReplacePlan(
            ops=[
                replace.ReplaceOp(
                    src=Path("/tmp/src.txt"),
                    dst=paths.Resolved(
                        path=Path("/tmp/static/collection/a.txt"),
                        dataset="tank/a/static/collection",
                    ),
                )
            ]
        )

        replace.execute_replace_plan(cx, plan)
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]

        self.assertEqual(args[0], cx)

        muts = args[1]
        self.assertEqual(len(muts), 1)

        mut = muts[0]
        self.assertIsInstance(mut, mutation.CopyMutation)
        self.assertEqual(mut.src, Path("/tmp/src.txt"))
        self.assertEqual(
            mut.dst,
            Path("/tmp/static/collection/a.txt"),
        )
        self.assertEqual(
            mut.dataset,
            "tank/a/static/collection",
        )

    @patch("pilo.fs.sha256_file", return_value="abc123")
    def test_replace_manifest_mutations(self, _):

        dst = paths.Resolved(
            path=Path("/pile/in/a.txt"),
            dataset="tank/pile",
        )
        op = replace.ReplaceOp(
            src=Path("/tmp/new.txt"),
            dst=dst,
        )
        plan = replace.ReplacePlan(ops=[op])

        muts = replace.build_manifest_mutations(plan, Path("/pile"))

        self.assertEqual(len(muts), 1)
        mut = muts[0]
        self.assertEqual(mut.subset, "pile")
        self.assertEqual(mut.entry.path, Path("in/a.txt"))
        self.assertEqual(mut.entry.checksum, "abc123")

    @patch("pilo.fs.sha256_file")
    def test_replace_execution_plan_builds_execution_plan(self, *_):

        cx = pilotest.make_context()

        resolved = cx.resolve(Path("in/a.txt"))

        plan = replace.ReplacePlan(
            ops=[
                replace.ReplaceOp(
                    src=Path("/tmp/src.txt"),
                    dst=resolved,
                )
            ]
        )

        exec_plan = replace.build_exec_plan(cx, plan)

        self.assertIsInstance(exec_plan, ExecutionPlan)
        self.assertEqual(len(exec_plan.filesystem_steps), 1)
        self.assertEqual(len(exec_plan.manifest_steps), 1)

    @patch("pilo.fs.sha256_file")
    def test_replace_execution_plan_contains_manifest_steps(self, *_):

        cx = pilotest.make_context()

        resolved = cx.resolve(Path("in/a.txt"))

        plan = replace.ReplacePlan(
            ops=[
                replace.ReplaceOp(
                    src=Path("/tmp/src.txt"),
                    dst=resolved,
                )
            ]
        )

        exec_plan = replace.build_exec_plan(cx, plan)

        op = exec_plan.manifest_steps[0]

        mpath = cx.admin_path / "manifest/pile.manifest"
        self.assertEqual(op.subset, "pile")
        self.assertEqual(op.manifest_path, mpath)
        self.assertEqual(len(op.build_mutations()), 1)
