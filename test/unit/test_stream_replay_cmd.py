from pathlib import Path
from unittest.mock import patch

from pilo.back.replay import ReplayPlan, ReplayResult
from pilo.back.streams import StreamManifest
from pilo import error
import pilotest


def _make_result(snapshot="20260522_010203_000000-incr",
                 source="tank/a", target="tank/b"):
    return ReplayResult(
        status="APPLIED",
        stream=snapshot + '.zfs',
        snapshot=snapshot,
        source=source,
        target_dataset=target,
        applied_at="2026-05-22T01:02:03+00:00",
    )


class TestStreamReplayCmd(pilotest.TestCase):

    @patch("sys.argv", ["pilo-stream-replay"])
    def test_no_args_exits(self):
        mod = pilotest.import_command("stream-replay")
        with pilotest.suppress_stderr():
            with self.assertRaises(SystemExit):
                mod.main()

    @patch("pilo.back.replay.build_replay_plan")
    @patch("sys.argv", ["pilo-stream-replay", "stream.zfs"])
    def test_defaults_target_to_source(self, mock_build):
        manifest = StreamManifest(
            stream="stream.zfs", snapshot="snap",
            source="tank/a", guid="123",
            checksum="abc", size=100,
            created="2026-05-22T01:02:03",
        )
        plan = ReplayPlan(
            stream_path=Path("stream.zfs"),
            manifest=manifest,
            target_dataset="tank/a",
        )
        mock_build.return_value = plan

        mod = pilotest.import_command("stream-replay")
        with patch("pilo.back.replay.execute_replay_plan",
                   return_value=_make_result()):
            with pilotest.suppress_stdout():
                mod.main()

        mock_build.assert_called_once_with("stream.zfs", None)

    @patch("pilo.back.replay.build_replay_plan")
    @patch("sys.argv", ["pilo-stream-replay", "stream.zfs", "tank/c"])
    def test_explicit_target(self, mock_build):
        manifest = StreamManifest(
            stream="stream.zfs", snapshot="snap",
            source="tank/a", guid="123",
            checksum="abc", size=100,
            created="2026-05-22T01:02:03",
        )
        plan = ReplayPlan(
            stream_path=Path("stream.zfs"),
            manifest=manifest,
            target_dataset="tank/c",
        )
        mock_build.return_value = plan

        mod = pilotest.import_command("stream-replay")
        with patch("pilo.back.replay.execute_replay_plan",
                   return_value=_make_result(target="tank/c")):
            with pilotest.suppress_stdout():
                mod.main()

        mock_build.assert_called_once_with("stream.zfs", "tank/c")

    @patch("sys.argv", ["pilo-stream-replay", "stream.zfs"])
    def test_build_failure_propagates(self):
        mod = pilotest.import_command("stream-replay")
        with patch("pilo.back.replay.build_replay_plan") as mock_build:
            mock_build.side_effect = error.FatalError("manifest not found")

            with self.assert_fatal():
                mod.main()

    @patch("pilo.back.replay.build_replay_plan")
    @patch("sys.argv", ["pilo-stream-replay", "stream.zfs"])
    def test_prints_result_line(self, mock_build):
        manifest = StreamManifest(
            stream="stream.zfs", snapshot="20260522_010203_000000-incr",
            source="tank/a", guid="123",
            checksum="abc", size=100,
            created="2026-05-22T01:02:03",
        )
        plan = ReplayPlan(
            stream_path=Path("stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )
        mock_build.return_value = plan

        with patch("pilo.back.replay.execute_replay_plan",
                   return_value=_make_result()):
            with patch("builtins.print") as mock_print:
                mod = pilotest.import_command("stream-replay")
                mod.main()

        mock_print.assert_called_once_with(
            "APPLIED 20260522_010203_000000-incr.zfs tank/b")
