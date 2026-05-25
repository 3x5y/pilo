import unittest
from unittest.mock import patch

from pilo import state
from pilo.storage import lifecycle
import pilotest


#state = lifecycle


class TestOperationalState(pilotest.TestCase):

    @patch("pilo.storage.normalize.validate_dataset_contracts")
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
        report = lifecycle.collect_validation_report(cx)
        self.assertEqual(len(report.by_code("missing.required.dataset")), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts")
    @patch("pilo.storage.replication.replication_status")
    def test_diverged_state(self, repl, validate, *_):
        validate.return_value = []
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()
        report = lifecycle.collect_validation_report(cx)
        self.assertEqual(len(report.by_code("replication.diverged")), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts")
    @patch("pilo.storage.replication.replication_status")
    def test_healthy_state(self, repl, validate, *_):
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        validate.return_value = []
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state():
            report = lifecycle.collect_validation_report(cx)

        self.assertTrue(report.is_healthy)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts")
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
            report = lifecycle.collect_validation_report(cx)

        issues = report.by_code("missing.required.dataset")
        self.assertEqual(len(issues), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts", return_value=[])
    def test_collect_validation_report_empty(self, validate, *_):
        with pilotest.healthy_system_state():
            cx = pilotest.make_context()
            report = lifecycle.collect_validation_report(cx)

        self.assertTrue(report.is_healthy)

    def test_collect_snapshot_validation_stale(self):
        cx = pilotest.make_context()
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "50"}

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=900, now=1000):
            with patch.dict("os.environ", env):
                issues = lifecycle.collect_snapshot_validation(cx)

        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.code, "snapshot.stale")
        self.assertEqual(issue.component, "snapshot")

    def test_collect_snapshot_validation_fresh(self):
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "50"}
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=990, now=1000):
            with patch.dict("os.environ", env):
                issues = lifecycle.collect_snapshot_validation(cx)

        self.assertEqual(issues, [])

    @patch("pilo.zfs.latest_snapshot_with_time")
    def test_collect_snapshot_validation_missing(self, mock_snap):
        mock_snap.return_value = (None, None)
        cx = pilotest.make_context()

        issues = lifecycle.collect_snapshot_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "snapshot.missing")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts")
    @patch("pilo.storage.replication.replication_status")
    def test_stale_snapshot_degraded_state(self, repl, validate, *_):
        validate.return_value = []
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        cx = pilotest.make_context()
        env = {"CONFIG_SNAPSHOT_MAX_AGE": "1"}

        with pilotest.healthy_snapshot_state('tank/test@r1', ts=0, now=1000):
            with patch.dict("os.environ", env):
                report = lifecycle.collect_validation_report(cx)

        #self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertEqual(len(report.by_code("snapshot.stale")), 1)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_collect_replication_validation_behind(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.BEHIND, "behind in tank/b")
        cx = pilotest.make_context()

        issues = lifecycle.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue.code, "replication.behind")
        self.assertEqual(issue.component, "replication")

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_collect_replication_validation_diverged(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.DIVERGED, "diverged")
        cx = pilotest.make_context()

        issues = lifecycle.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.diverged")
        self.assertEqual(issues[0].severity, state.ValidationSeverity.ERROR)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_collect_replication_validation_ok(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus
        repl.return_value = (ReplicationStatus.OK, None)
        cx = pilotest.make_context()

        issues = lifecycle.collect_replication_validation(cx)

        self.assertEqual(issues, [])

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.normalize.validate_dataset_contracts")
    @patch("pilo.storage.replication.replication_status")
    def test_replication_behind_degraded_state(self, repl, validate, *_):
        from pilo.storage.replication import ReplicationStatus
        validate.return_value = []
        repl.return_value = (ReplicationStatus.BEHIND, "behind")
        cx = pilotest.make_context()

        with pilotest.healthy_snapshot_state():
            report = lifecycle.collect_validation_report(cx)

        #self.assertEqual(st.state, state.OperationalState.DEGRADED)
        self.assertEqual(len(report.by_code("replication.behind")), 1)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    @patch("pilo.storage.replication.replication_status")
    def test_collect_replication_validation_unattached(self, repl, *_):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        issues = lifecycle.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.secondary_missing")
        repl.assert_not_called()

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_collect_replication_validation_missing_secondary(self, _):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )

        issues = lifecycle.collect_replication_validation(cx)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "replication.secondary_missing")

    @patch("pilo.storage.lifecycle.detect_lifecycle")
    def test_collect_replication_validation_uses_classifier(self, detect):
        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_BEHIND,
            message="behind",
        )
        cx = pilotest.make_context()
        issues = lifecycle.collect_replication_validation(cx)

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

        st = lifecycle.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            lifecycle.LifecycleState.REPLICA_MISSING,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_detect_system_state_normal(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus

        repl.return_value = (ReplicationStatus.OK, None)

        cx = pilotest.make_context()

        st = lifecycle.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            lifecycle.LifecycleState.NORMAL,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_detect_system_state_behind(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus

        repl.return_value = (
            ReplicationStatus.BEHIND,
            "behind",
        )

        cx = pilotest.make_context()

        st = lifecycle.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            lifecycle.LifecycleState.REPLICATION_BEHIND,
        )

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.storage.replication.replication_status")
    def test_detect_system_state_diverged(self, repl, *_):
        from pilo.storage.replication import ReplicationStatus

        repl.return_value = (
            ReplicationStatus.DIVERGED,
            "diverged",
        )

        cx = pilotest.make_context()

        st = lifecycle.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            lifecycle.LifecycleState.REPLICATION_DIVERGED,
        )

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_detect_system_state_invalid_topology(self, _exists):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="pool1/backup pool2/backup",
        )

        st = lifecycle.detect_lifecycle(cx)

        self.assertEqual(
            st.state,
            lifecycle.LifecycleState.INVALID_TOPOLOGY,
        )

    def test_replication_validation_issue_normal(self):

        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
        )

        issue = lifecycle.replication_validation_issue(st)

        self.assertIsNone(issue)

    def test_replication_validation_issue_diverged(self):

        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
            message="diverged",
        )

        issue = lifecycle.replication_validation_issue(st)

        self.assertEqual(issue.code, "replication.diverged")
        self.assertEqual(
            issue.severity,
            state.ValidationSeverity.ERROR,
        )

    def test_lifecycle_recoverable_normal(self):

        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
        )

        self.assertTrue(lifecycle.lifecycle_recoverable(st))

    def test_lifecycle_recoverable_missing(self):

        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_MISSING,
        )

        self.assertFalse(lifecycle.lifecycle_recoverable(st))

    def test_lifecycle_replication_degraded(self):

        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_BEHIND,
        )

        self.assertTrue(lifecycle.lifecycle_replication_degraded(st))


class TestLifecyclePredicates(pilotest.TestCase):

    def test_replication_permitted_normal(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
        )

        self.assertTrue(
            lifecycle.lifecycle_replication_permitted(st)
        )

    def test_replication_permitted_behind(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_BEHIND,
        )

        self.assertTrue(
            lifecycle.lifecycle_replication_permitted(st)
        )

    def test_replication_not_permitted_diverged(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertFalse(
            lifecycle.lifecycle_replication_permitted(st)
        )

    def test_recovery_permitted_uninitialized(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertTrue(
            lifecycle.lifecycle_recovery_permitted(st)
        )

    def test_recovery_not_permitted_invalid_topology(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.INVALID_TOPOLOGY,
        )

        self.assertFalse(
            lifecycle.lifecycle_recovery_permitted(st)
        )


class TestLifecycleLegality(pilotest.TestCase):

    def test_seed_replication_permitted(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
        )

        self.assertTrue(
            lifecycle.lifecycle_seed_replication_permitted(st)
        )

    def test_normal_replication_not_seed_permitted(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
        )

        self.assertFalse(
            lifecycle.lifecycle_seed_replication_permitted(st)
        )

    def test_requires_provisioning(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
        )

        self.assertTrue(
            lifecycle.lifecycle_requires_provisioning(st)
        )

    def test_replication_fault(self):
        st = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
        )

        self.assertTrue(
            lifecycle.lifecycle_has_replication_fault(st)
        )

    def test_lifecycle_replica_seed_permitted(self):
        ls = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
        )
        self.assertTrue(lifecycle.lifecycle_seed_replication_permitted(ls))

        ls = lifecycle.LifecycleStatus(state=lifecycle.LifecycleState.NORMAL)
        self.assertFalse(lifecycle.lifecycle_seed_replication_permitted(ls))

        ls = lifecycle.LifecycleStatus(state=lifecycle.LifecycleState.REPLICATION_BEHIND)
        self.assertFalse(lifecycle.lifecycle_seed_replication_permitted(ls))

        ls = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
        )
        self.assertFalse(lifecycle.lifecycle_seed_replication_permitted(ls))

    @patch("pilo.storage.lifecycle.detect_lifecycle")
    def test_recovery_permitted_unknown(self, detect):

        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.UNKNOWN,
            message="source has no snapshots",
            secondary="backup/a",
        )

        self.assertTrue(
            lifecycle.lifecycle_recovery_permitted(
                detect.return_value
            )
        )
