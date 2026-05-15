import unittest
from unittest.mock import patch

from pilo import state
from pilotest import make_context


class TestOperationalState(unittest.TestCase):

    @patch("pilo.normalize.validate_dataset_contracts")
    def test_incomplete_state(self, validate):

        validate.return_value = [
            state.StateIssue(
                "missing.required.dataset",
                "missing dataset",
            )
        ]

        cx = make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(
            st.state,
            state.OperationalState.INCOMPLETE,
        )

    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    def test_diverged_state(
        self,
        repl,
        validate,
    ):
        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (
            ReplicationStatus.DIVERGED,
            "diverged",
        )
        cx = make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(
            st.state,
            state.OperationalState.REPLICATION_DIVERGED,
        )

    @patch("pilo.normalize.validate_dataset_contracts")
    @patch("pilo.back.replication.replication_status")
    @patch("pilo.status.check_snapshot_status")
    def test_healthy_state(
        self,
        snapshot,
        repl,
        validate,
    ):

        validate.return_value = []
        from pilo.back.replication import ReplicationStatus
        repl.return_value = (
            ReplicationStatus.OK,
            None,
        )
        cx = make_context()
        st = state.derive_operational_state(cx)
        self.assertEqual(
            st.state,
            state.OperationalState.HEALTHY,
        )
