import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from pilo.back import stream_gc
from pilo.back.stream_gc import StreamGcOp, StreamGcPlan
from pilo.back.streams import MANIFEST_SUFFIX
import pilotest


class TestOldestHeldTimestamp(pilotest.TestCase):

    @patch("pilo.zfs.snapshots_userrefs", return_value=[])
    def test_empty(self, mock_urefs):
        self.assertIsNone(stream_gc.oldest_held_timestamp("tank"))

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260522_010203_000000-mark", 1),
    ])
    def test_found(self, mock_urefs):
        ts = stream_gc.oldest_held_timestamp("tank")
        self.assertEqual(ts, "20260522_010203_000000")

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260522_010203_000000-reg", 1),
        ("tank@20260522_020000_000000-mark", 1),
    ])
    def test_skips_non_mark(self, mock_urefs):
        ts = stream_gc.oldest_held_timestamp("tank")
        self.assertEqual(ts, "20260522_020000_000000")

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260101_000000_000000-mark", 0),
        ("tank@20260102_000000_000000-mark", 1),
    ])
    def test_skips_unheld(self, mock_urefs):
        ts = stream_gc.oldest_held_timestamp("tank")
        self.assertEqual(ts, "20260102_000000_000000")


class TestEffectiveTs(pilotest.TestCase):

    def test_reg_stream(self):
        self.assertEqual(
            stream_gc._effective_ts(Path("20260101_000000_000000-reg.zfs")),
            "20260101_000000_000000",
        )

    def test_mark_stream(self):
        self.assertEqual(
            stream_gc._effective_ts(Path("20260101_000000_000000-mark.zfs")),
            "20260101_000000_000000",
        )

    def test_full_stream(self):
        self.assertEqual(
            stream_gc._effective_ts(Path("20260101_000000_000000-full.zfs")),
            "20260101_000000_000000",
        )

    def test_rollup_stream(self):
        self.assertEqual(
            stream_gc._effective_ts(
                Path("20260101_000000_000000--20260102_000000_000000.rollup.zfs")),
            "20260102_000000_000000",
        )

    def test_no_timestamp(self):
        ts = stream_gc._effective_ts(Path("foo.zfs"))
        self.assertEqual(ts, "foo.zfs")

    def test_manifest_skipped(self):
        self.assertEqual(
            stream_gc._effective_ts(Path("20260101_000000_000000-reg.zfs.manifest")),
            "20260101_000000_000000",
        )


class TestStreamGcOp(pilotest.TestCase):

    def test_fields(self):
        op = StreamGcOp(
            stream_path=Path("/out/s.zfs"),
            manifest_path=Path("/out/s.zfs.manifest"),
        )
        self.assertEqual(op.stream_path, Path("/out/s.zfs"))
        self.assertEqual(op.manifest_path, Path("/out/s.zfs.manifest"))

    def test_frozen(self):
        op = StreamGcOp(stream_path=Path("/a"), manifest_path=None)
        with self.assertRaises(AttributeError):
            op.stream_path = "/b"


class TestStreamGcPlan(pilotest.TestCase):

    def test_empty(self):
        plan = StreamGcPlan(ops=())
        self.assertEqual(plan.ops, ())

    def test_with_ops(self):
        op = StreamGcOp(stream_path=Path("/a.zfs"), manifest_path=None)
        plan = StreamGcPlan(ops=(op,))
        self.assertEqual(len(plan.ops), 1)
        self.assertIs(plan.ops[0], op)

    def test_frozen(self):
        plan = StreamGcPlan(ops=())
        with self.assertRaises(AttributeError):
            plan.ops = (1,)


class TestBuildGcPlan(pilotest.TestCase):

    def _make_stream(self, tmpdir, ts, kind="reg"):
        d = Path(tmpdir) / ts[:8]
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{ts}-{kind}.zfs"
        path.touch()
        manifest = path.with_suffix(MANIFEST_SUFFIX)
        manifest.write_text("{}")
        return path

    def _make_rollup(self, tmpdir, a_ts, b_ts):
        d = Path(tmpdir) / b_ts[:8]
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{a_ts}--{b_ts}.rollup.zfs"
        path.touch()
        manifest = path.with_suffix(MANIFEST_SUFFIX)
        manifest.write_text("{}")
        return path

    @patch("pilo.zfs.snapshots_userrefs", return_value=[])
    def test_empty_plan_no_held(self, mock_urefs):
        plan = stream_gc.build_gc_plan("tank", "/out")
        self.assertEqual(len(plan.ops), 0)

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_empty_plan_all_newer(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_stream(tmp, "20260602_000000_000000", "reg")
            plan = stream_gc.build_gc_plan("tank", tmp)
            self.assertEqual(len(plan.ops), 0)

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_candidates_identified(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_stream(tmp, "20260531_000000_000000", "reg")
            self._make_stream(tmp, "20260601_000000_000000", "reg")
            plan = stream_gc.build_gc_plan("tank", tmp)
            self.assertEqual(len(plan.ops), 1)
            self.assertIn("20260531", str(plan.ops[0].stream_path))

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_keep_zero(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_stream(tmp, "20260530_000000_000000", "reg")
            self._make_stream(tmp, "20260531_000000_000000", "reg")
            plan = stream_gc.build_gc_plan("tank", tmp, keep=0)
            self.assertEqual(len(plan.ops), 2)

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_keep_one(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_stream(tmp, "20260530_000000_000000", "reg")
            self._make_stream(tmp, "20260531_000000_000000", "reg")
            plan = stream_gc.build_gc_plan("tank", tmp, keep=1)
            self.assertEqual(len(plan.ops), 1)
            self.assertIn("20260530", str(plan.ops[0].stream_path))

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_rollup_inside_boundary(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_rollup(tmp, "20260530_000000_000000",
                              "20260601_000000_000000")
            plan = stream_gc.build_gc_plan("tank", tmp)
            self.assertEqual(len(plan.ops), 0,
                             "rollup with B_ts == cutoff should be kept")

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_rollup_outside_boundary(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_rollup(tmp, "20260529_000000_000000",
                              "20260530_000000_000000")
            plan = stream_gc.build_gc_plan("tank", tmp)
            self.assertEqual(len(plan.ops), 1,
                             "rollup with B_ts < cutoff should be pruned")

    @patch("pilo.zfs.snapshots_userrefs", return_value=[
        ("tank@20260601_000000_000000-mark", 1),
    ])
    def test_manifest_path_none_when_missing(self, mock_urefs):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "20260531"
            d.mkdir(parents=True, exist_ok=True)
            path = d / "20260531_000000_000000-reg.zfs"
            path.touch()
            plan = stream_gc.build_gc_plan("tank", tmp)
            self.assertEqual(len(plan.ops), 1)
            self.assertIsNone(plan.ops[0].manifest_path)


class TestExecuteGcPlan(pilotest.TestCase):

    def test_empty_plan(self):
        plan = StreamGcPlan(ops=())
        results = list(stream_gc.execute_gc_plan(plan, "/out"))
        self.assertEqual(results, [])

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream_path = Path(tmp) / "s.zfs"
            stream_path.touch()
            manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
            manifest_path.touch()
            op = StreamGcOp(
                stream_path=stream_path,
                manifest_path=manifest_path,
            )
            plan = StreamGcPlan(ops=(op,))
            results = list(stream_gc.execute_gc_plan(plan, tmp))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], stream_path)
            self.assertFalse(stream_path.exists())
            self.assertFalse(manifest_path.exists())

    def test_delete_no_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream_path = Path(tmp) / "s.zfs"
            stream_path.touch()
            op = StreamGcOp(stream_path=stream_path, manifest_path=None)
            plan = StreamGcPlan(ops=(op,))
            results = list(stream_gc.execute_gc_plan(plan, tmp))
            self.assertEqual(len(results), 1)
            self.assertFalse(stream_path.exists())

    def test_delete_manifest_not_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream_path = Path(tmp) / "s.zfs"
            stream_path.touch()
            manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
            op = StreamGcOp(
                stream_path=stream_path, manifest_path=manifest_path)
            plan = StreamGcPlan(ops=(op,))
            results = list(stream_gc.execute_gc_plan(plan, tmp))
            self.assertEqual(len(results), 1)
            self.assertFalse(stream_path.exists())
            self.assertFalse(manifest_path.exists())

    def test_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream_path = Path(tmp) / "20260531" / "s.zfs"
            stream_path.parent.mkdir()
            stream_path.touch()
            manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
            manifest_path.touch()
            op = StreamGcOp(
                stream_path=stream_path,
                manifest_path=manifest_path,
            )
            plan = StreamGcPlan(ops=(op,))
            with tempfile.TemporaryDirectory() as gc:
                results = list(stream_gc.execute_gc_plan(
                    plan, tmp, gc_path=gc))
                self.assertEqual(len(results), 1)
                self.assertFalse(stream_path.exists())
                self.assertEqual(results[0], stream_path)
                expected = Path(gc) / "20260531" / "s.zfs"
                self.assertTrue(expected.exists())
                expected_m = Path(gc) / "20260531" / "s.zfs.manifest"
                self.assertTrue(expected_m.exists())

    @patch("pilo.back.stream_gc.shutil.move")
    def test_move_preserves_rel(self, mock_move):
        output_path = Path("/out")
        stream_path = output_path / "20260531" / "s.zfs"
        manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
        op = StreamGcOp(
            stream_path=stream_path, manifest_path=manifest_path)
        plan = StreamGcPlan(ops=(op,))
        with patch.object(Path, "mkdir"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pilo.back.stream_gc.open"):
                    list(stream_gc.execute_gc_plan(
                        plan, output_path, gc_path="/gc"))
        move_calls = [c.args for c in mock_move.call_args_list]
        self.assertIn(("/out/20260531/s.zfs", "/gc/20260531/s.zfs"),
                      move_calls)
        self.assertIn(
            ("/out/20260531/s.zfs.manifest",
             "/gc/20260531/s.zfs.manifest"),
            move_calls)

    def test_move_conflict_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream_path = Path(tmp) / "s.zfs"
            stream_path.touch()
            op = StreamGcOp(stream_path=stream_path, manifest_path=None)
            plan = StreamGcPlan(ops=(op,))
            with tempfile.TemporaryDirectory() as gc:
                dst = Path(gc) / "s.zfs"
                dst.touch()
                with pilotest.assert_fatal(self):
                    list(stream_gc.execute_gc_plan(
                        plan, tmp, gc_path=gc))

    def test_multiple_ops(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.zfs"
            p1.touch()
            p2 = Path(tmp) / "b.zfs"
            p2.touch()
            op1 = StreamGcOp(stream_path=p1, manifest_path=None)
            op2 = StreamGcOp(stream_path=p2, manifest_path=None)
            plan = StreamGcPlan(ops=(op1, op2))
            results = list(stream_gc.execute_gc_plan(plan, tmp))
            self.assertEqual(len(results), 2)
            self.assertFalse(p1.exists())
            self.assertFalse(p2.exists())
