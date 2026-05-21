from unittest.mock import call, patch, Mock

from pilo import lifecycle
import pilotest


class TestRotateGcCommand(pilotest.TestCase):

    def test_command_exists(self):
        mod = pilotest.import_command("rotate-gc")
        self.assertIsNotNone(mod)

    def test_requires_secondary(self):
        mod = pilotest.import_command("rotate-gc")
        cx = pilotest.make_context()

        p1 = patch(
            "pilo.lifecycle.detect_lifecycle",
            return_value=lifecycle.LifecycleStatus(
                state=lifecycle.LifecycleState.REPLICA_MISSING,
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
            "pilo.lifecycle.detect_lifecycle",
            return_value=lifecycle.LifecycleStatus(
                state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
                message="requires provisioning",
                secondary="pool1/backup",
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()

    @patch("builtins.print")
    @patch("pilo.back.continuity.ageing_plan")
    @patch("pilo.back.continuity.execute_ageing_plan")
    def test_preview_builds_plan(self, mock_execute, mock_plan, mock_print):
        mock_plan.return_value = Mock(
            secondary_to_prune=[],
            secondary_to_release=[],
            primary_to_prune=[],
            primary_to_release=[],
        )
        mod = pilotest.import_command("rotate-gc")
        cx = pilotest.make_context()
        cx.args = ["--preview"]

        p1 = patch(
            "pilo.lifecycle.detect_lifecycle",
            return_value=lifecycle.LifecycleStatus(
                state=lifecycle.LifecycleState.NORMAL,
                message="ok",
                secondary="pool1/backup",
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2):
            mod.main()

        mock_plan.assert_called_once()
        mock_execute.assert_not_called()

    @patch("builtins.print")
    @patch("pilo.back.continuity.preview_ageing_plan")
    @patch("pilo.back.continuity.ageing_plan")
    @patch("pilo.back.continuity.execute_ageing_plan")
    def test_preview_prints_output(
            self, mock_execute, mock_plan, mock_preview, mock_print,
    ):
        mock_preview.return_value = [
            "destroy sec@a",
            "release pilo:pool1 sec@b",
        ]
        mod = pilotest.import_command("rotate-gc")
        cx = pilotest.make_context()
        cx.args = ["--preview"]

        p1 = patch(
            "pilo.lifecycle.detect_lifecycle",
            return_value=lifecycle.LifecycleStatus(
                state=lifecycle.LifecycleState.NORMAL,
                message="ok",
                secondary="pool1/backup",
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2):
            mod.main()

        call_args = [call("destroy sec@a"), call("release pilo:pool1 sec@b")]
        self.assertEqual(mock_print.call_args_list, call_args)
        mock_execute.assert_not_called()
