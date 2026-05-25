import tempfile
from pathlib import Path
from unittest.mock import patch

from pilo.storage import replay
from pilo.storage.streams import StreamManifest, MANIFEST_SUFFIX
import pilotest


def _make_manifest(snapshot="20260522_010203_000000-reg",
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
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    plan = replay.build_replay_plan(str(stream_path))

                    self.assertEqual(plan.target_dataset, "tank/a")

    def test_uses_provided_target(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    plan = replay.build_replay_plan(
                        str(stream_path), target_dataset="tank/c")

                    self.assertEqual(plan.target_dataset, "tank/c")

    def test_missing_manifest_raises_fatal(self):
        with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
            stream_path = Path(f.name)

            with self.assert_fatal():
                replay.build_replay_plan(str(stream_path))

    def test_verify_failure_raises_fatal(self):
        manifest = _make_manifest()
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("MISMATCH", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
                    stream_path = Path(f.name)
                    manifest_path = stream_path.with_suffix(
                        MANIFEST_SUFFIX)
                    manifest_path.write_text("{}")

                    with self.assert_fatal():
                        replay.build_replay_plan(str(stream_path))

    def test_plan_fields(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
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

    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.snapshot_exists", return_value=False)
    @patch("pilo.zfs.recv_file")
    def test_calls_recv_file(self, mock_recv, mock_exists, mock_guid):
        manifest = _make_manifest(source="tank/a")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        result = replay.execute_replay_plan(plan)

        mock_recv.assert_called_once_with(
            Path("/out/stream.zfs"), "tank/b")
        mock_exists.assert_called_once_with(
            "tank/b@20260522_010203_000000-reg")

    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.snapshot_exists", return_value=False)
    @patch("pilo.zfs.recv_file")
    def test_returns_applied_result(self, mock_recv, mock_exists, mock_guid):
        manifest = _make_manifest(
            snapshot="20260522_010203_000000-reg", source="tank/a")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        result = replay.execute_replay_plan(plan)

        self.assertEqual(result.status, "APPLIED")
        self.assertEqual(result.snapshot, "20260522_010203_000000-reg")
        self.assertEqual(result.source, "tank/a")
        self.assertEqual(result.target_dataset, "tank/b")
        self.assertIsNotNone(result.applied_at)

    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.snapshot_exists", return_value=False)
    @patch("pilo.zfs.recv_file")
    def test_recv_failure_propagates(self, mock_recv, mock_exists, mock_guid):
        mock_recv.side_effect = RuntimeError("zfs receive failed")
        manifest = _make_manifest()
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        with self.assertRaises(RuntimeError):
            replay.execute_replay_plan(plan)

    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.recv_file")
    def test_skipped_when_snapshot_exists(self, mock_recv, mock_exists,
                                          mock_guid):
        mock_guid.return_value = "12345"
        manifest = _make_manifest(guid="12345")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        result = replay.execute_replay_plan(plan)

        self.assertEqual(result.status, "SKIPPED")
        self.assertEqual(result.snapshot, "20260522_010203_000000-reg")
        self.assertEqual(result.target_dataset, "tank/b")
        mock_recv.assert_not_called()

    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.recv_file")
    def test_fatal_on_guid_mismatch(self, mock_recv, mock_exists,
                                    mock_guid):
        mock_guid.return_value = "99999"
        manifest = _make_manifest(guid="12345")
        plan = replay.ReplayPlan(
            stream_path=Path("/out/stream.zfs"),
            manifest=manifest,
            target_dataset="tank/b",
        )

        with self.assert_fatal():
            replay.execute_replay_plan(plan)


class TestClassifyStreams(pilotest.TestCase):

    def test_is_rollup_stream_match_rollup_suffix(self):
        self.assertTrue(replay.is_rollup_stream(Path("a-rollup.zfs")))

    def test_is_rollup_stream_match_a_b_rollup(self):
        self.assertTrue(
            replay.is_rollup_stream(Path("a--b.rollup.zfs")))

    def test_is_rollup_stream_no_match_incr(self):
        self.assertFalse(
            replay.is_rollup_stream(Path("a-reg.zfs")))

    def test_is_rollup_stream_no_match_anchor(self):
        self.assertFalse(
            replay.is_rollup_stream(Path("a-mark.zfs")))

    def test_is_rollup_stream_no_match_plain(self):
        self.assertFalse(replay.is_rollup_stream(Path("a.zfs")))


class TestOrderStreams(pilotest.TestCase):

    def test_order_empty(self):
        self.assertEqual(replay.order_streams([]), [])

    def test_order_single_incr(self):
        p = Path("a-reg.zfs")
        self.assertEqual(replay.order_streams([p]), [p])

    def test_order_single_rollup(self):
        p = Path("a-rollup.zfs")
        self.assertEqual(replay.order_streams([p]), [p])

    def test_order_rollups_first(self):
        r1 = Path("b-rollup.zfs")
        r2 = Path("a-rollup.zfs")
        i1 = Path("d-reg.zfs")
        i2 = Path("c-reg.zfs")
        result = replay.order_streams([i1, r1, i2, r2])
        self.assertEqual(result, [r2, r1, i2, i1])

    def test_order_with_anchor(self):
        r = Path("r-rollup.zfs")
        a = Path("a-mark.zfs")
        i = Path("i-reg.zfs")
        result = replay.order_streams([i, r, a])
        self.assertEqual(result, [r, a, i])

    def test_order_sorted_within_bucket(self):
        r2 = Path("20260524_000000_000002-rollup.zfs")
        r1 = Path("20260524_000000_000001-rollup.zfs")
        i2 = Path("20260524_000000_000004-reg.zfs")
        i1 = Path("20260524_000000_000003-reg.zfs")
        result = replay.order_streams([i2, r2, i1, r1])
        self.assertEqual(result, [r1, r2, i1, i2])

    def test_order_non_canonical_last(self):
        r = Path("r-rollup.zfs")
        i = Path("i-reg.zfs")
        x = Path("x.zfs")
        y = Path("y.zfs")
        result = replay.order_streams([x, i, r, y])
        self.assertEqual(result, [r, i, x, y])


class TestFindStreams(pilotest.TestCase):

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            result = replay.find_streams(d)
            self.assertEqual(result, [])

    def test_single_stream_file(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "20260522_010203_000000-reg.zfs").touch()
            result = replay.find_streams(d)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name,
                             "20260522_010203_000000-reg.zfs")

    def test_lexical_ordering(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "b.zfs").touch()
            Path(d, "a.zfs").touch()
            Path(d, "c.zfs").touch()
            result = replay.find_streams(d)
            names = [p.name for p in result]
            self.assertEqual(names, ["a.zfs", "b.zfs", "c.zfs"])

    def test_manifest_files_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "stream.zfs").touch()
            Path(d, "stream.zfs.manifest").touch()
            result = replay.find_streams(d)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, "stream.zfs")

    def test_non_stream_files_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "stream.zfs").touch()
            Path(d, "notes.txt").touch()
            Path(d, "data.bin").touch()
            result = replay.find_streams(d)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, "stream.zfs")

    def test_mixed_contents_sorted(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "b.zfs").touch()
            Path(d, "a.zfs").touch()
            Path(d, "a.zfs.manifest").touch()
            Path(d, "readme.md").touch()
            result = replay.find_streams(d)
            names = [p.name for p in result]
            self.assertEqual(names, ["a.zfs", "b.zfs"])

    def test_recursive_discovery(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "root.zfs").touch()
            sub = Path(d, "20260101")
            sub.mkdir()
            Path(sub, "deep.zfs").touch()
            Path(sub, "deep.zfs.manifest").touch()
            Path(sub, "other.txt").touch()
            result = replay.find_streams(d)
            names = sorted(p.name for p in result)
            self.assertEqual(names, ["deep.zfs", "root.zfs"])


class TestBatchReplayPlan(pilotest.TestCase):

    def test_empty_plans(self):
        batch = replay.BatchReplayPlan(plans=())
        self.assertEqual(batch.plans, ())

    def test_with_plans(self):
        plan = replay.ReplayPlan(
            stream_path=Path("/s.zfs"), manifest="m", target_dataset="t")
        batch = replay.BatchReplayPlan(plans=(plan,))
        self.assertEqual(len(batch.plans), 1)
        self.assertIs(batch.plans[0], plan)

    def test_frozen(self):
        batch = replay.BatchReplayPlan(plans=())
        with self.assertRaises(AttributeError):
            batch.plans = (1, 2, 3)

    def test_tuple_immutable(self):
        plan = replay.ReplayPlan(
            stream_path=Path("/s.zfs"), manifest="m", target_dataset="t")
        batch = replay.BatchReplayPlan(plans=(plan,))
        with self.assertRaises(AttributeError):
            batch.plans = ()


class TestBuildBatchReplayPlan(pilotest.TestCase):

    def test_empty_paths(self):
        batch = replay.build_batch_replay_plan([])
        self.assertEqual(batch.plans, ())

    def test_single_path(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as f:
                    Path(f.name).with_suffix(
                        MANIFEST_SUFFIX).write_text("{}")

                    batch = replay.build_batch_replay_plan([f.name])

                    self.assertEqual(len(batch.plans), 1)
                    self.assertEqual(
                        batch.plans[0].target_dataset, "tank/a")

    def test_multiple_paths_ordered(self):
        with tempfile.TemporaryDirectory() as d:
            a_path = Path(d, "b-reg.zfs")
            b_path = Path(d, "a-reg.zfs")
            a_path.touch()
            b_path.touch()
            Path(d, "b-reg.zfs.manifest").write_text("{}")
            Path(d, "a-reg.zfs.manifest").write_text("{}")
            manifest = _make_manifest(source="tank/a")
            with patch("pilo.storage.replay.load_stream_manifest",
                       return_value=manifest):
                with patch("pilo.storage.replay.verify_one",
                           return_value=("OK", "")):
                    batch = replay.build_batch_replay_plan(
                        [str(a_path), str(b_path)])

                    self.assertEqual(len(batch.plans), 2)
                    # ordered lexically: a-reg.zfs < b-reg.zfs
                    self.assertEqual(
                        batch.plans[0].stream_path, b_path)
                    self.assertEqual(
                        batch.plans[1].stream_path, a_path)

    def test_target_passed_to_all_plans(self):
        manifest = _make_manifest(source="tank/a")
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("OK", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fa:
                    with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fb:
                        Path(fa.name).with_suffix(
                            MANIFEST_SUFFIX).write_text("{}")
                        Path(fb.name).with_suffix(
                            MANIFEST_SUFFIX).write_text("{}")

                        batch = replay.build_batch_replay_plan(
                            [fa.name, fb.name],
                            target_dataset="tank/b")

                        for plan in batch.plans:
                            self.assertEqual(
                                plan.target_dataset, "tank/b")

    def test_first_failure_stops_batch(self):
        with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fa:
            with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fb:
                # fa has no manifest → fatal on first path
                with self.assert_fatal():
                    replay.build_batch_replay_plan([fa.name, fb.name])

    def test_verify_failure_stops_batch(self):
        manifest = _make_manifest()
        with patch("pilo.storage.replay.load_stream_manifest",
                   return_value=manifest):
            with patch("pilo.storage.replay.verify_one",
                       return_value=("MISMATCH", "")):
                with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fa:
                    with tempfile.NamedTemporaryFile(prefix="pilo.tmp.", suffix=".zfs") as fb:
                        Path(fa.name).with_suffix(
                            MANIFEST_SUFFIX).write_text("{}")
                        Path(fb.name).with_suffix(
                            MANIFEST_SUFFIX).write_text("{}")

                        with self.assert_fatal():
                            replay.build_batch_replay_plan(
                                [fa.name, fb.name])


class TestExecuteBatchReplayPlan(pilotest.TestCase):

    def _snap_exists_false(self):
        return patch("pilo.zfs.snapshot_exists", return_value=False)

    def _guid_any(self):
        return patch("pilo.zfs.get_guid")

    @patch("pilo.zfs.recv_file")
    def test_empty_batch(self, mock_recv):
        batch = replay.BatchReplayPlan(plans=())
        results = list(replay.execute_batch_replay_plan(batch))
        self.assertEqual(results, [])
        mock_recv.assert_not_called()

    @patch("pilo.zfs.recv_file")
    def test_single_plan(self, mock_recv):
        plan = replay.ReplayPlan(
            stream_path=Path("/s.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        batch = replay.BatchReplayPlan(plans=(plan,))
        with self._snap_exists_false(), self._guid_any():
            results = list(replay.execute_batch_replay_plan(batch))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "APPLIED")
        mock_recv.assert_called_once_with(Path("/s.zfs"), "tank/a")

    @patch("pilo.zfs.recv_file")
    def test_multiple_plans_in_order(self, mock_recv):
        plan_a = replay.ReplayPlan(
            stream_path=Path("/a.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        plan_b = replay.ReplayPlan(
            stream_path=Path("/b.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        batch = replay.BatchReplayPlan(plans=(plan_a, plan_b))
        with self._snap_exists_false(), self._guid_any():
            results = list(replay.execute_batch_replay_plan(batch))
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0].snapshot, plan_a.manifest.snapshot)
        self.assertEqual(
            results[1].snapshot, plan_b.manifest.snapshot)

    @patch("pilo.zfs.recv_file")
    def test_first_failure_stops_batch(self, mock_recv):
        mock_recv.side_effect = [
            None, RuntimeError("second recv failed"), None,
        ]
        plan_a = replay.ReplayPlan(
            stream_path=Path("/a.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        plan_b = replay.ReplayPlan(
            stream_path=Path("/b.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        plan_c = replay.ReplayPlan(
            stream_path=Path("/c.zfs"), manifest=_make_manifest(),
            target_dataset="tank/a")
        batch = replay.BatchReplayPlan(
            plans=(plan_a, plan_b, plan_c))

        # plan_b fails → exception propagates, plan_c never reached
        with self._snap_exists_false(), self._guid_any():
            with self.assertRaises(RuntimeError):
                list(replay.execute_batch_replay_plan(batch))

        self.assertEqual(mock_recv.call_count, 2)
        mock_recv.assert_any_call(Path("/a.zfs"), "tank/a")
        mock_recv.assert_any_call(Path("/b.zfs"), "tank/a")
