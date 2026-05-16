import unittest
from unittest.mock import patch

from pilo import state
import pilotest


class TestOperationalState(pilotest.TestCase):

    @patch("pilo.normalize.validate_dataset_contracts")
    def test_incomplete_state(self, validate):
        from pilo.normalize import DatasetValidationIssue

        validate.return_value = [
            DatasetValidationIssue(
                dataset="tank/test",
                code="missing.required.dataset",
                message="missing dataset",
            )
        ]
        cx = pilotest.make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(st.state, state.OperationalState.INCOMPLETE)

    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_diverged_state(self, repl, validate):
        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(st.state, state.OperationalState.REPLICATION_DIVERGED)

    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_healthy_state(self, repl, validate):
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        validate.return_value = []
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state():
            st = state.derive_operational_state(cx)

        self.assertEqual(st.state, state.OperationalState.HEALTHY)

    @patch("pilo.normalize.validate_dataset_contracts")
    def test_collect_validation_report(self, validate, *_):
        from pilo.normalize import DatasetValidationIssue
        validate.return_value = [
            DatasetValidationIssue(
                dataset="tank/x",
                code="missing.required.dataset",
                message="missing dataset",
            )
        ]

        cx = pilotest.make_context()
        with pilotest.healthy_snapshot_state():
            report = state.collect_validation_report(cx)

        self.assertEqual(len(report.issues), 1)
        issue = report.issues[0]
        self.assertEqual(issue.code, "missing.required.dataset")
        self.assertEqual(issue.component, "datasets")

    @patch("pilo.normalize.validate_dataset_contracts", return_value=[])
    def test_collect_validation_report_empty(self, validate):
        with pilotest.healthy_snapshot_state():
            cx = pilotest.make_context()
            report = state.collect_validation_report(cx)

        self.assertEqual(report.issues, [])
        self.assertFalse(report.has_errors)

    def test_collect_snapshot_validation_stale(self):
        cx = pilotest.make_context()
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "50"}

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=900, now=1000):
            with patch.dict("os.environ", env):
                issues = state.collect_snapshot_validation(cx)

        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.code, "snapshot.stale")
        self.assertEqual(issue.component, "snapshot")

    def test_collect_snapshot_validation_fresh(self):
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "50"}
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=990, now=1000):
            with patch.dict("os.environ", env):
                issues = state.collect_snapshot_validation(cx)

        self.assertEqual(issues, [])

    @patch("pilo.zfs.latest_snapshot_with_time")
    def test_collect_snapshot_validation_missing(self, mock_snap):
        mock_snap.return_value = (None, None)
        cx = pilotest.make_context()

        issues = state.collect_snapshot_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "snapshot.missing")

    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_stale_snapshot_degraded_state(self, repl, validate):
        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        cx = pilotest.make_context()
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "1"}

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=0, now=1000):
            with patch.dict("os.environ", env):
                st = state.derive_operational_state(cx)

        self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertTrue(any(i.code == "snapshot.stale" for i in st.issues))
