import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pilo.back import rollups
from pilo.back.rollups import RollupOp, RollupPlan
import pilotest


class TestRollupOp(pilotest.TestCase):

    def test_fields(self):
        op = RollupOp(
            output_path=Path("/out/r.zfs"),
            base_snapshot="tank@20260101_000000_000000-mark",
            target_snapshot="tank@20260102_000000_000000-mark",
            source_dataset="tank",
        )
        self.assertEqual(op.output_path, Path("/out/r.zfs"))
        self.assertEqual(
            op.base_snapshot, "tank@20260101_000000_000000-mark")

    def test_frozen(self):
        op = RollupOp(
            output_path=Path("/out/r.zfs"),
            base_snapshot="tank@a", target_snapshot="tank@b",
            source_dataset="tank",
        )
        with self.assertRaises(AttributeError):
            op.output_path = "/other"


class TestRollupPlan(pilotest.TestCase):

    def test_empty_ops(self):
        plan = RollupPlan(ops=())
        self.assertEqual(plan.ops, ())

    def test_with_ops(self):
        op = RollupOp(
            output_path=Path("/out/r.zfs"),
            base_snapshot="tank@a", target_snapshot="tank@b",
            source_dataset="tank",
        )
        plan = RollupPlan(ops=(op,))
        self.assertEqual(len(plan.ops), 1)
        self.assertIs(plan.ops[0], op)

    def test_frozen(self):
        plan = RollupPlan(ops=())
        with self.assertRaises(AttributeError):
            plan.ops = (1, 2, 3)

    def test_tuple_immutable(self):
        op = RollupOp(
            output_path=Path("/out/r.zfs"),
            base_snapshot="tank@a", target_snapshot="tank@b",
            source_dataset="tank",
        )
        plan = RollupPlan(ops=(op,))
        with self.assertRaises(AttributeError):
            plan.ops = ()


class TestRollupFilename(pilotest.TestCase):

    def test_rollup_filename(self):
        result = rollups.rollup_filename(
            "20260101_000000_000000-mark",
            "20260102_000000_000000-mark",
        )
        self.assertEqual(
            result,
            "20260101_000000_000000--20260102_000000_000000.rollup.zfs",
        )

    def test_rollup_filename_same_date(self):
        result = rollups.rollup_filename(
            "20260101_010000_000000-mark",
            "20260101_020000_000000-mark",
        )
        self.assertEqual(
            result,
            "20260101_010000_000000--20260101_020000_000000.rollup.zfs",
        )


class TestRollupOutputPath(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_output_path_date_dir(self):
        result = rollups.rollup_output_path(
            "20260102_000000_000000-mark",
            "20260101--20260102.rollup.zfs",
        )
        self.assertEqual(
            result,
            Path("/out/20260102/20260101--20260102.rollup.zfs"),
        )


class TestDiscoverRollupChain(pilotest.TestCase):

    @patch("pilo.zfs.list_snapshots", return_value=[])
    def test_no_snapshots(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(pairs, [])

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-mark",
    ])
    def test_one_mark(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(pairs, [])

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-mark",
        "tank@20260102_000000_000000-mark",
    ])
    def test_two_marks_one_pair(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(len(pairs), 1)
        self.assertEqual(
            pairs[0],
            ("20260101_000000_000000-mark",
             "20260102_000000_000000-mark"),
        )

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-mark",
        "tank@20260101_010000_000000-reg",
        "tank@20260102_000000_000000-mark",
        "tank@20260102_010000_000000-reg",
        "tank@20260103_000000_000000-mark",
    ])
    def test_three_marks_two_pairs(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][0], "20260101_000000_000000-mark")
        self.assertEqual(pairs[0][1], "20260102_000000_000000-mark")
        self.assertEqual(pairs[1][0], "20260102_000000_000000-mark")
        self.assertEqual(pairs[1][1], "20260103_000000_000000-mark")

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-mark",
        "tank@20260102_000000_000000-mark",
        "tank@20260103_000000_000000-mark",
    ])
    def test_chronological_order(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(len(pairs), 2)
        self.assertEqual(
            pairs[0],
            ("20260101_000000_000000-mark",
             "20260102_000000_000000-mark"),
        )
        self.assertEqual(
            pairs[1],
            ("20260102_000000_000000-mark",
             "20260103_000000_000000-mark"),
        )

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-reg",
        "tank@20260102_000000_000000-reg",
    ])
    def test_non_mark_ignored(self, mock_list):
        pairs = rollups.discover_rollup_chain("tank")
        self.assertEqual(pairs, [])


class TestBuildRollupPlan(pilotest.TestCase):

    def _make_snaps(self, *names):
        return [f"tank@{n}" for n in names]

    @patch("pilo.zfs.list_snapshots", return_value=[])
    def test_empty_plan(self, mock_list):
        plan = rollups.build_rollup_plan("tank")
        self.assertEqual(len(plan.ops), 0)

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@20260101_000000_000000-mark",
        "tank@20260102_000000_000000-mark",
    ])
    def test_builds_one_op(self, mock_list):
        with patch("pilo.back.rollups.verify_one",
                   return_value=("NOT_FOUND", "")):
            with patch.dict(os.environ,
                            {"PILO_STREAM_OUTPUT_PATH": "/out"}):
                plan = rollups.build_rollup_plan("tank")
        self.assertEqual(len(plan.ops), 1)
        op = plan.ops[0]
        self.assertEqual(
            op.base_snapshot,
            "tank@20260101_000000_000000-mark",
        )
        self.assertEqual(
            op.target_snapshot,
            "tank@20260102_000000_000000-mark",
        )
        self.assertEqual(op.source_dataset, "tank")
        self.assertIn("20260101_000000_000000"
                      "--20260102_000000_000000.rollup.zfs",
                      str(op.output_path))

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@a-mark",
        "tank@b-mark",
    ])
    def test_skip_existing_verified(self, mock_list):
        with patch("pilo.back.rollups.verify_one",
                   return_value=("OK", "")):
            with patch("pilo.back.rollups.stream_output_path",
                       return_value=Path("/out")):
                with patch.object(Path, "exists",
                                  return_value=True):
                    plan = rollups.build_rollup_plan("tank")
        self.assertEqual(len(plan.ops), 0)

    @patch("pilo.zfs.list_snapshots", return_value=[
        "tank@a-mark",
        "tank@b-mark",
    ])
    def test_skip_existing_corrupt_regenerates(self, mock_list):
        with patch("pilo.back.rollups.verify_one",
                   return_value=("MISMATCH", "")):
            with patch.dict(os.environ,
                            {"PILO_STREAM_OUTPUT_PATH": "/out"}):
                with patch.object(Path, "exists",
                                  return_value=True):
                    plan = rollups.build_rollup_plan("tank")
        self.assertEqual(len(plan.ops), 1)


class TestExecuteRollupPlan(pilotest.TestCase):

    def test_empty_plan(self):
        plan = RollupPlan(ops=())
        results = list(rollups.execute_rollup_plan(plan))
        self.assertEqual(results, [])

    @patch("pilo.back.rollups.write_rollup_manifest")
    @patch("pilo.zfs.get_guid", return_value="guid123")
    @patch("pilo.zfs.send_incremental_to_file")
    def test_single_op(self, mock_send, mock_guid, mock_manifest):
        op = RollupOp(
            output_path=Path("/out/r.zfs"),
            base_snapshot="tank@base-mark",
            target_snapshot="tank@target-mark",
            source_dataset="tank",
        )
        plan = RollupPlan(ops=(op,))
        results = list(rollups.execute_rollup_plan(plan))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], Path("/out/r.zfs"))
        mock_send.assert_called_once_with(
            "tank@base-mark", "tank@target-mark",
            Path("/out/r.zfs"),
        )
        mock_guid.assert_called_once_with("tank@target-mark")
        mock_manifest.assert_called_once_with(
            Path("/out/r.zfs"),
            snapshot_name="target-mark",
            source="tank",
            guid="guid123",
            base_snapshot="base-mark",
        )

    @patch("pilo.back.rollups.write_rollup_manifest")
    @patch("pilo.zfs.get_guid", return_value="g")
    @patch("pilo.zfs.send_incremental_to_file")
    def test_multiple_ops(self, mock_send, mock_guid, mock_manifest):
        op1 = RollupOp(
            output_path=Path("/out/r1.zfs"),
            base_snapshot="tank@a", target_snapshot="tank@b",
            source_dataset="tank",
        )
        op2 = RollupOp(
            output_path=Path("/out/r2.zfs"),
            base_snapshot="tank@b", target_snapshot="tank@c",
            source_dataset="tank",
        )
        plan = RollupPlan(ops=(op1, op2))
        results = list(rollups.execute_rollup_plan(plan))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], Path("/out/r1.zfs"))
        self.assertEqual(results[1], Path("/out/r2.zfs"))
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(mock_manifest.call_count, 2)
