import unittest
from unittest.mock import patch

import pilo
import pilotest


class TestRestorePlan(unittest.TestCase):

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_build_restore_plan_ok(self, mock_exists, mock_snap_exists):
        plan = pilo.build_restore_plan(
            src="tank/a",
            dst="tank/b",
            snap="r-123",
            recursive=False,
        )

        self.assertEqual(plan.src_snapshot, "tank/a@r-123")
        self.assertEqual(plan.dst, "tank/b")
        self.assertFalse(plan.recursive)

    @patch("pilo.zfs.snapshot_exists", return_value=False)
    def test_restore_plan_requires_snapshot(self, _):
        with pilotest.assert_fatal(self):
            pilo.build_restore_plan(
                "tank/a", "tank/b", "nope", False
            )

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_snapshot_must_match_source(self, mock_exists, _):
        with pilotest.assert_fatal(self):
            pilo.build_restore_plan(
                "tank/a",
                "tank/b",
                "backup/x@r-1",  # invalid
                False,
            )

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_restore_plan_requires_new_dst(self, mock_exists, _):
        with pilotest.assert_fatal(self):
            pilo.build_restore_plan(
                "tank/a", "tank/b", "r-1", False
            )

    @patch("pilo.back.restore.restore_dataset")
    def test_execute_restore_plan(self, mock_restore):
        plan = pilo.RestorePlan(
            src_snapshot="tank/a@r-1",
            dst="tank/b",
            recursive=True,
        )

        pilo.execute_restore_plan(plan)

        mock_restore.assert_called_once_with(
            "tank/a@r-1",
            "tank/b",
            recursive=True,
        )

    @patch("pilo.execute_restore_plan")
    @patch("pilo.build_restore_plan")
    def test_restore_command(self, mock_build, mock_exec):
        cx = pilotest.make_context()

        with patch("pilo.Context", return_value=cx):
            with patch.object(cx, "args", ["tank/a", "tank/b", "r-1"]):
                mod = pilotest.import_command('restore')
                mod.main()

        mock_build.assert_called_once_with("tank/a", "tank/b", "r-1", False)
        mock_exec.assert_called_once()
