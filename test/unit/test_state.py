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

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_diverged_state(self, repl, validate, *_):
        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(st.state, state.OperationalState.REPLICATION_DIVERGED)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_healthy_state(self, repl, validate, *_):
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        validate.return_value = []
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state():
            st = state.derive_operational_state(cx)

        self.assertEqual(st.state, state.OperationalState.HEALTHY)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
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
        with pilotest.healthy_system_state():
            report = state.collect_validation_report(cx)

        self.assertEqual(len(report.issues), 1)
        issue = report.issues[0]
        self.assertEqual(issue.code, "missing.required.dataset")
        self.assertEqual(issue.component, "datasets")

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts", return_value=[])
    def test_collect_validation_report_empty(self, validate, *_):
        with pilotest.healthy_system_state():
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

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_stale_snapshot_degraded_state(self, repl, validate, *_):
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

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_collect_replication_validation_behind(self, repl, *_):
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.BEHIND, "behind in tank/b")
        cx = pilotest.make_context()

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.code, "replication.behind")
        self.assertEqual(issue.component, "replication")

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_collect_replication_validation_diverged(self, repl, *_):
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.diverged")
        self.assertEqual(issues[0].severity, state.ValidationSeverity.ERROR)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_collect_replication_validation_ok(self, repl, *_):
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        cx = pilotest.make_context()

        issues = state.collect_replication_validation(cx)

        self.assertEqual(issues, [])

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_replication_behind_degraded_state(self, repl, validate, *_):
        from pilo.back.replication import ReplicationStatus
        validate.return_value = []
        repl.return_value = (ReplicationStatus.BEHIND, "behind")
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state():
            st = state.derive_operational_state(cx)

        self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertTrue(any(i.code=="replication.behind" for i in st.issues))

    @patch("pilo.zfs.dataset_exists", return_value=False)
    @patch("pilo.back.replication.replication_status")
    def test_collect_replication_validation_unattached(self, repl, *_):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0].code,
            "replication.secondary_missing",
        )
        repl.assert_not_called()

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_collect_replication_validation_missing_secondary(self, _):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0].code,
            "replication.secondary_missing",
        )

    @patch("pilo.state.detect_system_state")
    def test_collect_replication_validation_uses_classifier(self, detect):
        detect.return_value = state.DetectedSystemState(
            state=state.SystemTopologyState.REPLICATION_BEHIND,
            message="behind",
        )
        cx = pilotest.make_context()
        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0].code,
            "replication.behind",
        )

        detect.assert_called_once_with(cx)

class TestSystemClassifier(pilotest.TestCase):

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_detect_system_state_missing_secondary(self, _exists):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        st = state.detect_system_state(cx)

        self.assertEqual(
            st.state,
            state.SystemTopologyState.REPLICA_MISSING,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_detect_system_state_normal(self, repl, *_):
        from pilo.back.replication import ReplicationStatus

        repl.return_value = (ReplicationStatus.OK, None)

        cx = pilotest.make_context()

        st = state.detect_system_state(cx)

        self.assertEqual(
            st.state,
            state.SystemTopologyState.NORMAL,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_detect_system_state_behind(self, repl, *_):
        from pilo.back.replication import ReplicationStatus

        repl.return_value = (
            ReplicationStatus.BEHIND,
            "behind",
        )

        cx = pilotest.make_context()

        st = state.detect_system_state(cx)

        self.assertEqual(
            st.state,
            state.SystemTopologyState.REPLICATION_BEHIND,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_detect_system_state_diverged(self, repl, *_):
        from pilo.back.replication import ReplicationStatus

        repl.return_value = (
            ReplicationStatus.DIVERGED,
            "diverged",
        )

        cx = pilotest.make_context()

        st = state.detect_system_state(cx)

        self.assertEqual(
            st.state,
            state.SystemTopologyState.REPLICATION_DIVERGED,
        )

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_detect_system_state_invalid_topology(self, _exists):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a backup/b",
        )

        st = state.detect_system_state(cx)

        self.assertEqual(
            st.state,
            state.SystemTopologyState.INVALID_TOPOLOGY,
        )
