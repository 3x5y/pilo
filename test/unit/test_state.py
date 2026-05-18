import unittest
from unittest.mock import patch

from pilo import state
import pilotest


class TestOperationalState(pilotest.TestCase):

    @patch("pilo.normalize.validate_dataset_contracts")
    def test_incomplete_state(self, validate):
        validate.return_value = [
            state.ValidationIssue(
                code="missing.required.dataset",
                message="missing dataset tank/test",
                severity=state.ValidationSeverity.ERROR,
                component="datasets",
            )
        ]
        cx = pilotest.make_context()
        report = state.collect_validation_report(cx)
        self.assertEqual(len(report.by_code("missing.required.dataset")), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_diverged_state(self, repl, validate, *_):
        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()
        report = state.collect_validation_report(cx)
        self.assertEqual(len(report.by_code("replication.diverged")), 1)

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
            report = state.collect_validation_report(cx)

        self.assertTrue(report.is_healthy)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts")
    def test_collect_validation_report(self, validate, *_):
        validate.return_value = [
            state.ValidationIssue(
                code="missing.required.dataset",
                message=f"missing dataset tank/x",
                severity=state.ValidationSeverity.ERROR,
                component="datasets",
            )
        ]

        cx = pilotest.make_context()
        with pilotest.healthy_system_state():
            report = state.collect_validation_report(cx)

        issues = report.by_code("missing.required.dataset")
        self.assertEqual(len(issues), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.normalize.validate_dataset_contracts", return_value=[])
    def test_collect_validation_report_empty(self, validate, *_):
        with pilotest.healthy_system_state():
            cx = pilotest.make_context()
            report = state.collect_validation_report(cx)

        self.assertTrue(report.is_healthy)

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
                report = state.collect_validation_report(cx)

        #self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertEqual(len(report.by_code("snapshot.stale")), 1)

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
            report = state.collect_validation_report(cx)

        #self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertEqual(len(report.by_code("replication.behind")), 1)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    @patch("pilo.back.replication.replication_status")
    def test_collect_replication_validation_unattached(self, repl, *_):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.secondary_missing")
        repl.assert_not_called()

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_collect_replication_validation_missing_secondary(self, _):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )

        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.secondary_missing")

    @patch("pilo.state.detect_lifecycle")
    def test_collect_replication_validation_uses_classifier(self, detect):
        detect.return_value = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_BEHIND,
            message="behind",
        )
        cx = pilotest.make_context()
        issues = state.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.behind")
        detect.assert_called_once_with(cx)

    def test_validation_report_error_exit_code(self):
        cx = pilotest.make_context()
        report = state.ValidationReport()
        report.extend([
            state.ValidationIssue(
                code="foo.bar",
                message="bad condition",
                severity=state.ValidationSeverity.ERROR,
                component="foo",
            )
        ])

        self.assertEqual(report.exit_code, 1)


    def test_validation_report_warning_exit_code(self):
        cx = pilotest.make_context()
        report = state.ValidationReport()
        report.extend([
            state.ValidationIssue(
                code="foo.bar",
                message="less bad",
                severity=state.ValidationSeverity.WARN,
                component="foo",
            )
        ])

        self.assertEqual(report.exit_code, 1)


class TestSystemClassifier(pilotest.TestCase):

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_detect_system_state_missing_secondary(self, _exists):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        st = state.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            state.LifecycleState.REPLICA_MISSING,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.replication_status")
    def test_detect_system_state_normal(self, repl, *_):
        from pilo.back.replication import ReplicationStatus

        repl.return_value = (ReplicationStatus.OK, None)

        cx = pilotest.make_context()

        st = state.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            state.LifecycleState.NORMAL,
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

        st = state.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            state.LifecycleState.REPLICATION_BEHIND,
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

        st = state.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            state.LifecycleState.REPLICATION_DIVERGED,
        )

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_detect_system_state_invalid_topology(self, _exists):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a backup/b",
        )

        st = state.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            state.LifecycleState.INVALID_TOPOLOGY,
        )

    def test_replication_validation_issue_normal(self):

        lifecycle = state.LifecycleStatus(
            state=state.LifecycleState.NORMAL,
        )

        issue = state.replication_validation_issue(lifecycle)

        self.assertIsNone(issue)

    def test_replication_validation_issue_diverged(self):

        lifecycle = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_DIVERGED,
            message="diverged",
        )

        issue = state.replication_validation_issue(lifecycle)

        self.assertEqual(issue.code, "replication.diverged")
        self.assertEqual(
            issue.severity,
            state.ValidationSeverity.ERROR,
        )

    def test_lifecycle_recoverable_normal(self):

        lifecycle = state.LifecycleStatus(
            state=state.LifecycleState.NORMAL,
        )

        self.assertTrue(state.lifecycle_recoverable(lifecycle))

    def test_lifecycle_recoverable_missing(self):

        lifecycle = state.LifecycleStatus(
            state=state.LifecycleState.REPLICA_MISSING,
        )

        self.assertFalse(state.lifecycle_recoverable(lifecycle))

    def test_lifecycle_replication_degraded(self):

        lifecycle = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_BEHIND,
        )

        self.assertTrue(state.lifecycle_replication_degraded(lifecycle))


class TestLifecyclePredicates(pilotest.TestCase):

    def test_replication_permitted_normal(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.NORMAL,
        )

        self.assertTrue(
            state.lifecycle_replication_permitted(st)
        )

    def test_replication_permitted_behind(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_BEHIND,
        )

        self.assertTrue(
            state.lifecycle_replication_permitted(st)
        )

    def test_replication_not_permitted_diverged(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertFalse(
            state.lifecycle_replication_permitted(st)
        )

    def test_recovery_permitted_uninitialized(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertTrue(
            state.lifecycle_recovery_permitted(st)
        )

    def test_recovery_not_permitted_invalid_topology(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.INVALID_TOPOLOGY,
        )

        self.assertFalse(
            state.lifecycle_recovery_permitted(st)
        )


class TestLifecycleLegality(pilotest.TestCase):

    def test_seed_replication_permitted(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICA_UNINITIALIZED,
        )

        self.assertTrue(
            state.lifecycle_seed_replication_permitted(st)
        )

    def test_normal_replication_not_seed_permitted(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.NORMAL,
        )

        self.assertFalse(
            state.lifecycle_seed_replication_permitted(st)
        )

    def test_requires_provisioning(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICA_UNINITIALIZED,
        )

        self.assertTrue(
            state.lifecycle_requires_provisioning(st)
        )

    def test_replication_fault(self):
        st = state.LifecycleStatus(
            state=state.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertTrue(
            state.lifecycle_has_replication_fault(st)
        )
