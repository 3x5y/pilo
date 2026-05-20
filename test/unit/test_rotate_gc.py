from unittest.mock import patch

from pilo import state
import pilotest


class TestRotateGcCommand(pilotest.TestCase):

    def test_command_exists(self):
        mod = pilotest.import_command("rotate-gc")
        self.assertIsNotNone(mod)

    def test_requires_secondary(self):
        mod = pilotest.import_command("rotate-gc")
        cx = pilotest.make_context()

        p1 = patch(
            "pilo.state.detect_lifecycle",
            return_value=state.LifecycleStatus(
                state=state.LifecycleState.REPLICA_MISSING,
                message="no secondary",
                secondary=None,
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()

    def test_requires_provisioning(self):
        mod = pilotest.import_command("rotate-gc")
        cx = pilotest.make_context()

        p1 = patch(
            "pilo.state.detect_lifecycle",
            return_value=state.LifecycleStatus(
                state=state.LifecycleState.REPLICA_UNINITIALIZED,
                message="requires provisioning",
                secondary="pool1/backup",
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()
