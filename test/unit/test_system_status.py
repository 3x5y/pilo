import subprocess
import unittest
from unittest.mock import patch

from pilo import state
from pilo import status
import pilotest


class TestSystemStatusModel(pilotest.TestCase):

    def test_empty_status_is_ok(self):
        st = status.SystemStatus()

        self.assertEqual(st.code, 0)
        self.assertEqual(st.messages, [])

    def test_status_message_model(self):
        msg = status.StatusMessage(
            level="WARN",
            category="snapshot",
            message="stale",
        )

        self.assertEqual(msg.level, "WARN")
        self.assertEqual(msg.category, "snapshot")
        self.assertEqual(msg.message, "stale")

    @unittest.skip("dead code")
    @patch("pilo.back.replication.replication_status")
    @patch("pilo.zfs.latest_snapshot")
    def test_replication_ok(self, mock_snap, mock_repl):
        mock_snap.side_effect = ["tank/a@r1", "backup/a@r1"]
        from pilo.back.replication import ReplicationStatus
        mock_repl.return_value = (ReplicationStatus.OK, None)

        cx = pilotest.make_context()
        st = status.SystemStatus()

        status.check_replication_status(cx, st)

        self.assertIn(
            status.StatusMessage(
                level="OK",
                category="replication",
                message="r1",
            ),
            st.messages,
        )

    @unittest.skip("dead code")
    @patch("pilo.zfs.latest_snapshot_with_time")
    @patch("pilo.util.now_epoch", return_value=1000)
    def test_snapshot_fresh(self, mock_now, mock_snap):
        mock_snap.return_value = ("tank/a@r1", 990)

        cx = pilotest.make_context()
        st = status.SystemStatus()

        status.check_snapshot_status(cx, st, max_age=20)

        self.assertIn(
                status.StatusMessage(
                    level="OK",
                    category="snapshot",
                    message="fresh (10 s)",
                    ),
                st.messages,
                )

    @unittest.skip('dead code')
    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_missing_dataset(self, _):
        cx = pilotest.make_context()
        st = status.SystemStatus()

        status.check_dataset_status(cx, st)

        self.assertTrue(any(m.category == "missing.required.dataset" for m in st.messages))

    @patch("pilo.git.is_dirty", return_value=True)
    def test_dirty_repo(self, _):
        with pilotest.make_tmp_context() as cx:
            st = status.SystemStatus()

            # simulate one repo
            (cx.admin_path / "repo" / ".git").mkdir(parents=True, exist_ok=True)

            status.check_transient_status(cx, st)

            self.assertTrue(any(m.category == "transient" for m in st.messages))

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.check_transient_status")
    def test_collect_system_status_uses_validation_report(
        self,
        transient,
        collect,
    ):
        collect.return_value = state.ValidationReport()

        cx = pilotest.make_context()

        st = status.collect_system_status(cx)

        self.assertIsInstance(st,status.SystemStatus)
        inc = {"datasets", "snapshot", "replication"}
        collect.assert_called_once_with(cx, include=inc)
        transient.assert_called_once()

    def test_render_status_message(self):
        msg = status.StatusMessage(
            level="WARN",
            category="snapshot",
            message="stale",
        )

        rendered = status.render_status_message(msg)

        self.assertEqual(
            rendered,
            "WARN: snapshot: stale",
        )

    def test_manifest_status_missing_manifest_is_ok(self):
        cx = pilotest.make_context()
        st = status.SystemStatus()

        status.collect_manifest_status(cx, st, "pile")

        self.assertEqual(st.code, 0)

    @patch("subprocess.run")
    def test_manifest_status_ok(self, mock_run):
        with pilotest.make_tmp_context() as cx:
            st = status.SystemStatus()

            manifest = cx.admin_path / "manifest" / "pile.manifest"

            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("abc\n")

            status.collect_manifest_status(cx, st, "pile")

            sm = status.StatusMessage(level="OK",
                                    category="manifest",
                                    message="pile verified")
            self.assertIn(sm, st.messages)

    @patch("subprocess.run")
    def test_manifest_status_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["sha256sum"],
        )

        with pilotest.make_tmp_context() as cx:
            st = status.SystemStatus()

            manifest = cx.admin_path / "manifest" / "pile.manifest"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("abc\n")

            status.collect_manifest_status(cx, st, "pile")

            self.assertEqual(st.code, 1)
            sm = status.StatusMessage(level="WARN",
                                    category="manifest",
                                    message="pile verification failed")
            self.assertIn(sm, st.messages)

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.collect_manifest_status")
    def test_collect_calls_manifest(self, mock_manifest, *_):
        cx = pilotest.make_context()

        status.collect_system_status(cx)

        mock_manifest.assert_any_call(cx, unittest.mock.ANY, "pile")
        mock_manifest.assert_any_call(cx, unittest.mock.ANY, "collection")
        mock_manifest.assert_any_call(cx, unittest.mock.ANY, "filing")

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.collect_manifest_status")
    def test_collect_manifest_only(self, mock_manifest, *_):
        cx = pilotest.make_context()

        status.collect_system_status(cx, check="manifest")

        self.assertEqual(mock_manifest.call_count, 3)

    def test_validation_issues_rendered_into_messages(self):
        report = state.ValidationReport(
            issues=[
                state.ValidationIssue(
                    code="snapshot.stale",
                    message="snapshot stale",
                    severity=state.ValidationSeverity.WARN,
                    component="snapshot",
                )
            ]
        )

        msgs = status.validation_report_to_status_messages(report)

        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0],
            status.StatusMessage(
                level="WARN",
                category="snapshot.stale",
                message="snapshot stale",
            )
        )

@unittest.skip('dead code')
class TestStatusRegistry(pilotest.TestCase):

    def test_status_checks_order(self):
        names = [
            check.name
            for check in status.status_checks.ALL
        ]

        self.assertEqual(
            names,
            [
                "transient",
                "pile",
                "snapshot",
                "replication",
                "datasets",
                "manifest",
            ],
        )

    def test_status_check_lookup(self):
        check = status.status_checks.lookup("snapshot")

        self.assertEqual(check.name, "snapshot")
        self.assertEqual(
            check.func,
            status.check_snapshot_status,
        )

    def test_unknown_status_check_returns_none(self):
        self.assertIsNone(
            status.status_checks.lookup("missing")
        )
