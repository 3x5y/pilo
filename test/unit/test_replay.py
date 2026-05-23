import tempfile
from pathlib import Path
from unittest.mock import patch

from pilo.back import replay
from pilo.back.streams import StreamManifest, MANIFEST_SUFFIX
import pilotest


def _make_manifest(snapshot="20260522_010203_000000-incr",
                   source="tank/a", guid="12345"):
    return StreamManifest(
        stream=f"20260522/{snapshot}.zfs",
        snapshot=snapshot,
        source=source,
        guid=guid,
        checksum="abc",
        size=100,
        created="2026-05-22T01:02:03",
    )


class TestBuildReplayPlan(pilotest.TestCase):

    def test_defaults_target_to_source(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.back.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.back.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    plan = replay.build_replay_plan(str(stream_path))

                    self.assertEqual(plan.target_dataset, "tank/a")

    def test_uses_provided_target(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.back.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.back.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    plan = replay.build_replay_plan(
                        str(stream_path), target_dataset="tank/c")

                    self.assertEqual(plan.target_dataset, "tank/c")

    def test_missing_manifest_raises_fatal(self):
        with tempfile.NamedTemporaryFile(suffix=".zfs") as f:
            stream_path = Path(f.name)

            with self.assert_fatal():
                replay.build_replay_plan(str(stream_path))

    def test_verify_failure_raises_fatal(self):
        manifest = _make_manifest()
        with patch("pilo.back.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.back.replay.verify_one",
                       return_value=("MISMATCH", "")):
                with tempfile.NamedTemporaryFile(suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    with self.assert_fatal():
                        replay.build_replay_plan(str(stream_path))

    def test_plan_fields(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.back.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.back.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    plan = replay.build_replay_plan(
                        str(stream_path), target_dataset="tank/b")

                    self.assertEqual(plan.stream_path, stream_path)
                    self.assertIs(plan.manifest, manifest)
                    self.assertEqual(plan.target_dataset, "tank/b")


class TestExecuteReplayPlan(pilotest.TestCase):

    @patch("pilo.zfs.recv_file")
    def test_calls_recv_file(self, mock_recv):
        manifest = _make_manifest(source="tank/a")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        result = replay.execute_replay_plan(plan)

        mock_recv.assert_called_once_with(
            Path("/out/stream.zfs"), "tank/b")

    @patch("pilo.zfs.recv_file")
    def test_returns_applied_result(self, mock_recv):
        manifest = _make_manifest(
            snapshot="20260522_010203_000000-incr", source="tank/a")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        result = replay.execute_replay_plan(plan)

        self.assertEqual(result.status, "APPLIED")
        self.assertEqual(result.snapshot, "20260522_010203_000000-incr")
        self.assertEqual(result.source, "tank/a")
        self.assertEqual(result.target_dataset, "tank/b")
        self.assertIsNotNone(result.applied_at)

    @patch("pilo.zfs.recv_file")
    def test_recv_failure_propagates(self, mock_recv):
        mock_recv.side_effect = RuntimeError("zfs receive failed")
        manifest = _make_manifest()
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        with self.assertRaises(RuntimeError):
            replay.execute_replay_plan(plan)
