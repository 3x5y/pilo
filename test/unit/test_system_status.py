import unittest
from unittest.mock import patch

import pilo
from pilotest import make_context


class TestSystemStatusModel(unittest.TestCase):

    def test_empty_status_is_ok(self):
        st = pilo.SystemStatus()

        self.assertEqual(st.code, 0)
        self.assertEqual(st.messages, [])

    @patch("pilo.zfs.latest_snapshot")
    def test_replication_ok(self, mock_snap):
        mock_snap.side_effect = ["tank/a@r1", "backup/a@r1"]

        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_replication_status(cx, st)

        self.assertIn(("OK", "replication: r1"), st.messages)

    @patch("pilo.zfs.latest_snapshot_with_time")
    @patch("pilo.now_epoch", return_value=1000)
    def test_snapshot_fresh(self, mock_now, mock_snap):
        mock_snap.return_value = ("tank/a@r1", 990)

        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_snapshot_status(cx, st, max_age=20)

        self.assertIn(("OK", "snapshot: fresh (10 s)"), st.messages)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_missing_dataset(self, _):
        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_dataset_status(cx, st)

        self.assertTrue(any("missing dataset" in msg for _, msg in st.messages))

    @patch("pilo.git_dirty", return_value=True)
    def test_dirty_repo(self, _):
        cx = make_context()
        st = pilo.SystemStatus()

        # simulate one repo
        (cx.admin_path / "repo" / ".git").mkdir(parents=True, exist_ok=True)

        pilo.check_transient_status(cx, st)

        self.assertTrue(any("transient" in msg for _, msg in st.messages))

    @patch("pilo.check_replication_status")
    @patch("pilo.check_snapshot_status")
    @patch("pilo.check_dataset_status")
    @patch("pilo.check_transient_status")
    def test_collect_calls_all(self, t, d, s, r):
        cx = make_context()

        st = pilo.collect_system_status(cx)

        self.assertIsInstance(st, pilo.SystemStatus)
        r.assert_called_once()
        s.assert_called_once()
        d.assert_called_once()
        t.assert_called_once()
