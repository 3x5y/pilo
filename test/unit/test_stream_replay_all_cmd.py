from pathlib import Path
from unittest.mock import patch

from pilo.back.replay import (
    BatchReplayPlan,
    ReplayPlan,
    ReplayResult,
)
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


def _make_manifest():
    return StreamManifest(
        stream="20260522/20260522_010203_000000-incr.zfs",
        snapshot="20260522_010203_000000-incr",
        source="tank/a", guid="123",
        checksum="abc", size=100,
        created="2026-05-22T01:02:03",
    )


class TestStreamReplayAllCmd(pilotest.TestCase):

    @patch("sys.argv", ["pilo-stream-replay-all"])
    def test_no_args_exits(self):
        mod = pilotest.import_command("stream-replay-all")
        with pilotest.suppress_stderr():
            with self.assertRaises(SystemExit):
                mod.main()

    @patch("pilo.back.replay.find_streams")
    @patch("sys.argv", ["pilo-stream-replay-all", "/streams"])
    def test_empty_directory_returns_silently(self, mock_find):
        mock_find.return_value = []

        mod = pilotest.import_command("stream-replay-all")
        with patch("pilo.back.replay.build_batch_replay_plan") as mock_build:
            mod.main()
            mock_build.assert_not_called()

        mock_find.assert_called_once_with("/streams")

    @patch("pilo.back.replay.find_streams")
    @patch("sys.argv", ["pilo-stream-replay-all", "/streams", "tank/c"])
    def test_target_passed_to_batch(self, mock_find):
        mock_find.return_value = [Path("/streams/a.zfs")]
        manifest = _make_manifest()
        plan = ReplayPlan(
            stream_path=Path("/streams/a.zfs"),
            manifest=manifest,
            target_dataset="tank/c",
        )
        batch = BatchReplayPlan(plans=(plan,))

        mod = pilotest.import_command("stream-replay-all")
        with patch("pilo.back.replay.build_batch_replay_plan",
                   return_value=batch):
            with patch("pilo.back.replay.execute_batch_replay_plan",
                       return_value=[_make_result(target="tank/c")]):
                with pilotest.suppress_stdout():
                    mod.main()

        mock_find.assert_called_once_with("/streams")

    @patch("pilo.back.replay.find_streams")
    @patch("sys.argv", ["pilo-stream-replay-all", "/streams"])
    def test_prints_result_per_stream(self, mock_find):
        mock_find.return_value = [
            Path("/streams/a.zfs"), Path("/streams/b.zfs"),
        ]
        manifest = _make_manifest()
        plan_a = ReplayPlan(
            stream_path=Path("/streams/a.zfs"),
            manifest=manifest, target_dataset="tank/b",
        )
        plan_b = ReplayPlan(
            stream_path=Path("/streams/b.zfs"),
            manifest=manifest, target_dataset="tank/b",
        )
        batch = BatchReplayPlan(plans=(plan_a, plan_b))

        mod = pilotest.import_command("stream-replay-all")
        with patch("pilo.back.replay.build_batch_replay_plan",
                   return_value=batch):
            with patch("pilo.back.replay.execute_batch_replay_plan",
                       return_value=[
                           _make_result(
                               snapshot="20260522_010203_000000-incr",
                               target="tank/b"),
                           _make_result(
                               snapshot="20260522_010204_000000-incr",
                               target="tank/b"),
                       ]):
                with patch("builtins.print") as mock_print:
                    mod.main()

        calls = mock_print.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            str(calls[0]),
            "call('APPLIED 20260522_010203_000000-incr.zfs tank/b')")
        self.assertEqual(
            str(calls[1]),
            "call('APPLIED 20260522_010204_000000-incr.zfs tank/b')")

    @patch("pilo.back.replay.find_streams")
    @patch("sys.argv", ["pilo-stream-replay-all", "/streams"])
    def test_build_failure_propagates(self, mock_find):
        mock_find.return_value = [Path("/streams/bad.zfs")]

        mod = pilotest.import_command("stream-replay-all")
        with patch("pilo.back.replay.build_batch_replay_plan") as mock_build:
            mock_build.side_effect = error.FatalError(
                "stream verification failed")

            with self.assert_fatal():
                mod.main()

    @patch("pilo.back.replay.find_streams")
    @patch("sys.argv", ["pilo-stream-replay-all", "/streams"])
    def test_execute_failure_propagates(self, mock_find):
        mock_find.return_value = [Path("/streams/bad.zfs")]
        manifest = _make_manifest()
        plan = ReplayPlan(
            stream_path=Path("/streams/bad.zfs"),
            manifest=manifest, target_dataset="tank/a",
        )
        batch = BatchReplayPlan(plans=(plan,))

        mod = pilotest.import_command("stream-replay-all")
        with patch("pilo.back.replay.build_batch_replay_plan",
                   return_value=batch):
            with patch(
                "pilo.back.replay.execute_batch_replay_plan"
            ) as mock_exec:
                mock_exec.side_effect = RuntimeError(
                    "zfs receive failed")

                with self.assertRaises(RuntimeError):
                    mod.main()
