import subprocess
import unittest
from unittest.mock import patch

import pilo
from pilotest import make_context


class TestSystemStatusModel(unittest.TestCase):

    def test_empty_status_is_ok(self):
        st = pilo.SystemStatus()

        self.assertEqual(st.code, 0)
        self.assertEqual(st.messages, [])

    def test_status_message_model(self):
        msg = pilo.StatusMessage(
            level="WARN",
            category="snapshot",
            message="stale",
        )

        self.assertEqual(msg.level, "WARN")
        self.assertEqual(msg.category, "snapshot")
        self.assertEqual(msg.message, "stale")

    @patch("pilo.zfs.latest_snapshot")
    def test_replication_ok(self, mock_snap):
        mock_snap.side_effect = ["tank/a@r1", "backup/a@r1"]

        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_replication_status(cx, st)

        self.assertIn(
            pilo.StatusMessage(
                level="OK",
                category="replication",
                message="r1",
            ),
            st.messages,
        )

    @patch("pilo.zfs.latest_snapshot_with_time")
    @patch("pilo.now_epoch", return_value=1000)
    def test_snapshot_fresh(self, mock_now, mock_snap):
        mock_snap.return_value = ("tank/a@r1", 990)

        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_snapshot_status(cx, st, max_age=20)

        self.assertIn(
                pilo.StatusMessage(
                    level="OK",
                    category="snapshot",
                    message="fresh (10 s)",
                    ),
                st.messages,
                )

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_missing_dataset(self, _):
        cx = make_context()
        st = pilo.SystemStatus()

        pilo.check_dataset_status(cx, st)

        self.assertTrue(any(m.category == "incomplete" for m in st.messages))

    @patch("pilo.git_dirty", return_value=True)
    def test_dirty_repo(self, _):
        cx = make_context()
        st = pilo.SystemStatus()

        # simulate one repo
        (cx.admin_path / "repo" / ".git").mkdir(parents=True, exist_ok=True)

        pilo.check_transient_status(cx, st)

        self.assertTrue(any(m.category == "transient" for m in st.messages))

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

    def test_render_status_message(self):
        msg = pilo.StatusMessage(
            level="WARN",
            category="snapshot",
            message="stale",
        )

        rendered = pilo.render_status_message(msg)

        self.assertEqual(
            rendered,
            "WARN: snapshot: stale",
        )

    @patch("subprocess.run")
    def test_manifest_status_missing_manifest_is_ok(self, _):
        cx = make_context()
        st = pilo.SystemStatus()

        pilo.collect_manifest_status(cx, st, "pile")

        self.assertEqual(st.code, 0)

    @patch("subprocess.run")
    def test_manifest_status_ok(self, mock_run):
        cx = make_context()
        st = pilo.SystemStatus()

        manifest = cx.admin_path / "manifest" / "pile.manifest"

        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("abc\n")

        pilo.collect_manifest_status(cx, st, "pile")

        sm = pilo.StatusMessage(level="OK",
                                category="manifest",
                                message="pile verified")
        self.assertIn(sm, st.messages)

    @patch("subprocess.run")
    def test_manifest_status_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["sha256sum"],
        )

        cx = make_context()
        st = pilo.SystemStatus()

        manifest = cx.admin_path / "manifest" / "pile.manifest"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("abc\n")

        pilo.collect_manifest_status(cx, st, "pile")

        self.assertEqual(st.code, 1)
        sm = pilo.StatusMessage(level="WARN",
                                category="manifest",
                                message="pile verification failed")
        self.assertIn(sm, st.messages)
