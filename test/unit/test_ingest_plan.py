import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo import mutation
from pilo.front import ingest
import pilotest


class TestIngestOps(unittest.TestCase):

    def test_ingest_plan_model(self):
        plan = ingest.IngestPlan(
            ops=[
                ingest.IngestOp(
                    src=Path("/tmp/a"),
                    dst=Path("/tmp/b"),
                    dataset="tank/a/pile",
                    action="move",
                )
            ]
        )

        self.assertEqual(len(plan.ops), 1)
        self.assertEqual(plan.ops[0].action, "move")

    def test_build_ingest_plan(self):
        cx = pilotest.make_context()

        with tempfile.TemporaryDirectory() as td:
            intake = Path(td) / "intake"
            pile = Path(td) / "pile"

            intake.mkdir()
            pile.mkdir()

            src = intake / "a.txt"
            src.write_text("hello")

            cx.intake_path = intake
            cx.pile_path = pile

            plan = ingest.build_ingest_plan(cx, [src])

            self.assertEqual(len(plan.ops), 1)

            op = plan.ops[0]

            self.assertEqual(op.src, src)
            self.assertEqual(
                op.dst,
                pile / "in" / "a.txt",
            )
            self.assertEqual(op.action, "move")

    def test_ingest_plan_mutations(self):
        cx = pilotest.make_context()

        plan = ingest.IngestPlan(
            ops=[
                ingest.IngestOp(
                    src=Path("/tmp/in/a"),
                    dst=Path("/tmp/pile/in/a"),
                    action="move",
                    dataset=cx.pile_dataset,
                ),
                ingest.IngestOp(
                    src=Path("/tmp/in/b"),
                    dst=Path("/tmp/pile/in/b"),
                    action="noop",
                    dataset=cx.pile_dataset,
                ),
            ]
        )

        muts = ingest.ingest_plan_mutations(plan)

        self.assertEqual(len(muts), 2)

        self.assertIsInstance(muts[0], mutation.MoveMutation)
        self.assertIsInstance(muts[1], mutation.UnlinkMutation)

    def test_build_ingest_ops_new_file(self):
        cx = pilotest.make_context()

        with tempfile.TemporaryDirectory() as td:
            intake = Path(td) / "intake"
            pile = Path(td) / "pile"

            intake.mkdir()
            pile.mkdir()

            src = intake / "a.txt"
            src.write_text("hello")

            cx.intake_path = intake
            cx.pile_path = pile

            plan = ingest.build_ingest_plan(cx, [src])

            self.assertEqual(len(plan.ops), 1)

            op = plan.ops[0]

            self.assertEqual(op.src, src)
            self.assertEqual(
                op.dst,
                pile / "in" / "a.txt",
            )
            self.assertEqual(op.action, "move")

    @patch("pilo.fs.files_equal", return_value=True)
    def test_build_ingest_ops_identical_file_is_noop(self, _):
        cx = pilotest.make_context()

        with tempfile.TemporaryDirectory() as td:
            intake = Path(td) / "intake"
            pile = Path(td) / "pile"

            intake.mkdir()
            (pile / "in").mkdir(parents=True)

            src = intake / "a.txt"
            src.write_text("hello")

            dst = pile / "in" / "a.txt"
            dst.write_text("hello")

            cx.intake_path = intake
            cx.pile_path = pile

            plan = ingest.build_ingest_plan(cx, [src])

            self.assertEqual(len(plan.ops), 1)
            self.assertEqual(plan.ops[0].action, "noop")

    @patch("pilo.fs.files_equal", return_value=False)
    def test_build_ingest_ops_conflict_fails(self, _):
        cx = pilotest.make_context()

        with tempfile.TemporaryDirectory() as td:
            intake = Path(td) / "intake"
            pile = Path(td) / "pile"

            intake.mkdir()
            (pile / "in").mkdir(parents=True)

            src = intake / "a.txt"
            src.write_text("new")

            dst = pile / "in" / "a.txt"
            dst.write_text("old")

            cx.intake_path = intake
            cx.pile_path = pile

            with pilotest.assert_fatal(self):
                ingest.build_ingest_plan(cx, [src])

    @patch("pilo.fs.safe_move")
    @patch("pilo.zfs.dataset_writable")
    def test_execute_ingest_ops_moves_files(
        self,
        mock_writable,
        mock_move,
    ):
        cx = pilotest.make_context()

        mock_writable.return_value.__enter__.return_value = None
        mock_writable.return_value.__exit__.return_value = None

        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=Path("/tmp/in/a.txt"),
                    dst=Path("/tmp/pile/in/a.txt"),
                    action="move",
                    dataset=cx.pile_dataset,
                )
            ]
        )

        ingest.execute_ingest_plan(cx, plan)

        mock_writable.assert_called_once_with(cx.pile_dataset)

        mock_move.assert_called_once_with(
            cx,
            Path("/tmp/in/a.txt"),
            Path("/tmp/pile/in/a.txt"),
        )

    @patch("pathlib.Path.unlink")
    @patch("pilo.zfs.dataset_writable")
    def test_execute_ingest_ops_unlinks_noop_files(
        self,
        mock_writable,
        mock_unlink,
    ):
        cx = pilotest.make_context()

        mock_writable.return_value.__enter__.return_value = None
        mock_writable.return_value.__exit__.return_value = None

        src = Path("/tmp/in/a.txt")

        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=src,
                    dst=Path("/tmp/pile/in/a.txt"),
                    action="noop",
                    dataset=cx.pile_dataset,
                )
            ]
        )

        ingest.execute_ingest_plan(cx, plan)

        mock_unlink.assert_called_once_with()

    @patch("pilo.fs.safe_move")
    @patch("pilo.zfs.dataset_writable")
    def test_execute_ingest_ops_batches_writable_context(
        self,
        mock_writable,
        mock_move,
    ):
        cx = pilotest.make_context()

        mock_writable.return_value.__enter__.return_value = None
        mock_writable.return_value.__exit__.return_value = None

        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=Path("/tmp/in/a.txt"),
                    dst=Path("/tmp/pile/in/a.txt"),
                    action="move",
                    dataset=cx.pile_dataset,
                ),
                ingest.IngestOp(
                    src=Path("/tmp/in/b.txt"),
                    dst=Path("/tmp/pile/in/b.txt"),
                    action="move",
                    dataset=cx.pile_dataset,
                ),
            ]
        )

        ingest.execute_ingest_plan(cx, plan)

        mock_writable.assert_called_once_with(cx.pile_dataset)
        self.assertEqual(mock_move.call_count, 2)

    def test_ingest_mutations(self):
        cx = pilotest.make_context()
        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=Path("/tmp/in/a"),
                    dst=Path("/tmp/pile/in/a"),
                    action="move",
                    dataset=cx.pile_dataset,
                ),
                ingest.IngestOp(
                    src=Path("/tmp/in/b"),
                    dst=Path("/tmp/pile/in/b"),
                    action="noop",
                    dataset=cx.pile_dataset,
                ),
            ]
        )

        muts = ingest.ingest_plan_mutations(plan)

        self.assertEqual(len(muts), 2)

        self.assertIsInstance(muts[0], mutation.MoveMutation)
        self.assertIsInstance(muts[1], mutation.UnlinkMutation)

    @patch("pilo.mutation.execute_semantic_mutations")
    def test_execute_uses_executor(self, mock_exec):
        cx = pilotest.make_context()

        plan = ingest.IngestPlan(
            ops = [
                ingest.IngestOp(
                    src=Path("/tmp/a"),
                    dst=Path("/tmp/b"),
                    action="move",
                    dataset=cx.pile_dataset,
                )
            ]
        )

        ingest.execute_ingest_plan(cx, plan)

        mock_exec.assert_called_once()

    @patch("pilo.manifest.execute_manifest_update_plan")
    @patch("pilo.manifest.build_manifest_update_plan")
    @patch("pilo.front.ingest.execute_ingest_plan")
    @patch("pilo.front.ingest.build_ingest_plan")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_ingest_command_uses_plans(
        self,
        _exists,
        mock_build_ingest,
        mock_exec_ingest,
        mock_build_manifest,
        mock_exec_manifest,
    ):
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command("ingest-pile")
            mod.main()

        mock_build_ingest.assert_called_once()
        mock_exec_ingest.assert_called_once()

        mock_build_manifest.assert_called_once_with(
            cx,
            ["pile"],
        )

        mock_exec_manifest.assert_called_once()
