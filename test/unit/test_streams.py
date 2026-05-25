import os
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.back import streams
from pilo.back.snapshot import SnapshotKind, SnapshotName
import pilotest


class TestStreamOutputPath(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/some/streams"})
    def test_reads_env(self):
        self.assertEqual(streams.stream_output_path(), Path("/some/streams"))

    @patch.dict(os.environ, {}, clear=True)
    def test_unset_env_raises_fatal(self):
        with self.assert_fatal():
            streams.stream_output_path()

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": ""}, clear=True)
    def test_empty_env_raises_fatal(self):
        with self.assert_fatal():
            streams.stream_output_path()


class TestStreamFilename(pilotest.TestCase):

    def test_reg(self):
        self.assertEqual(
            streams.stream_filename("20260522_010203_000000", "reg"),
            "20260522_010203_000000-reg.zfs",
        )

    def test_mark(self):
        self.assertEqual(
            streams.stream_filename("20260522_010203_000000", "mark"),
            "20260522_010203_000000-mark.zfs",
        )

    def test_extra(self):
        self.assertEqual(
            streams.stream_filename("20260522_010203_000000", "extra"),
            "20260522_010203_000000-extra.zfs",
        )


class TestStreamDateDir(pilotest.TestCase):

    def test_extracts_first_eight_chars(self):
        self.assertEqual(
            streams.stream_date_dir("20260522_010203_000000"), "20260522"
        )

    def test_pads_short_string(self):
        self.assertEqual(streams.stream_date_dir("abc"), "abc")


class TestStreamFilepath(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_full_path_reg(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.REG)
        result = streams.stream_filepath(snap)
        self.assertEqual(
            result, Path("/out/20260522/20260522_010203_000000-reg.zfs")
        )

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_full_path_mark(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.MARK)
        result = streams.stream_filepath(snap)
        self.assertEqual(
            result, Path("/out/20260522/20260522_010203_000000-mark.zfs")
        )

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_full_path_extra(self):
        snap = SnapshotName(
            "20260522_010203_000000", SnapshotKind.EXTRA, "mylabel"
        )
        result = streams.stream_filepath(snap)
        self.assertEqual(
            result, Path("/out/20260522/20260522_010203_000000-extra.zfs")
        )


class TestExportIncrementalStream(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.back.streams.zfs.get_guid", return_value="guid123")
    @patch("pilo.back.streams.zfs.send_full_to_file")
    def test_full_export_no_base(self, mock_send, mock_guid, mock_manifest):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.REG)
        result = streams.export_incremental_stream("tank/a", snap)

        expected_path = Path(
            "/out/20260522/20260522_010203_000000-reg.zfs"
        )
        self.assertEqual(result, expected_path)
        mock_send.assert_called_once_with(
            "tank/a@20260522_010203_000000-reg",
            expected_path,
        )
        mock_guid.assert_called_once_with(
            "tank/a@20260522_010203_000000-reg"
        )
        mock_manifest.assert_called_once_with(
            expected_path,
            "20260522_010203_000000-reg",
            "tank/a",
            "guid123",
            kind="full", base_snapshot=None,
        )

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.back.streams.zfs.get_guid", return_value="guid456")
    @patch("pilo.back.streams.zfs.send_incremental_to_file")
    def test_reg_export_with_base(self, mock_send, mock_guid, mock_manifest):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.REG)
        base = SnapshotName(
            "20260522_010000_000000", SnapshotKind.MARK
        )
        result = streams.export_incremental_stream(
            "tank/a", snap, base=base,
        )

        expected_path = Path(
            "/out/20260522/20260522_010203_000000-reg.zfs"
        )
        self.assertEqual(result, expected_path)
        mock_send.assert_called_once_with(
            "tank/a@20260522_010000_000000-mark",
            "tank/a@20260522_010203_000000-reg",
            expected_path,
        )
        mock_guid.assert_called_once_with(
            "tank/a@20260522_010203_000000-reg"
        )
        mock_manifest.assert_called_once_with(
            expected_path,
            "20260522_010203_000000-reg",
            "tank/a",
            "guid456",
            kind="incremental",
            base_snapshot="20260522_010000_000000-mark",
        )


class TestStreamManifest(pilotest.TestCase):

    def test_manifest_fields(self):
        m = streams.StreamManifest(
            stream="20260522/20260522_010203_000000-reg.zfs",
            snapshot="20260522_010203_000000-reg",
            source="tank/a",
            guid="1234567890abcdef",
            checksum="abc" * 20,
            size=4096,
            created="2026-05-22T01:02:03.123456+00:00",
        )
        self.assertEqual(m.stream, "20260522/20260522_010203_000000-reg.zfs")
        self.assertEqual(m.size, 4096)

    def test_to_dict(self):
        m = streams.StreamManifest(
            stream="20260522/s.zfs",
            snapshot="ts-reg",
            source="tank/a",
            guid="guid",
            checksum="chk",
            size=100,
            created="2026-01-01T00:00:00+00:00",
        )
        d = m.to_dict()
        self.assertEqual(d["stream"], "20260522/s.zfs")
        self.assertEqual(d["size"], 100)
        self.assertEqual(d["snapshot"], "ts-reg")

    def test_from_dict(self):
        d = {
            "stream": "20260522/s.zfs",
            "snapshot": "ts-reg",
            "source": "tank/a",
            "guid": "guid",
            "checksum": "chk",
            "size": 100,
            "created": "2026-01-01T00:00:00+00:00",
        }
        m = streams.StreamManifest.from_dict(d)
        self.assertEqual(m.stream, "20260522/s.zfs")
        self.assertEqual(m.size, 100)
        self.assertIsInstance(m.size, int)

    def test_from_dict_missing_field(self):
        with self.assertRaises(ValueError):
            streams.StreamManifest.from_dict({"stream": "s.zfs"})

    def test_from_dict_size_not_int(self):
        with self.assertRaises(ValueError):
            streams.StreamManifest.from_dict({
                "stream": "s.zfs", "snapshot": "s", "source": "t",
                "guid": "g", "checksum": "c", "size": "not_int",
                "created": "now",
            })

    def test_roundtrip(self):
        m1 = streams.StreamManifest(
            stream="20260522/s.zfs",
            snapshot="ts-reg",
            source="tank/a",
            guid="abc123",
            checksum="def456",
            size=777,
            created="2026-06-06T06:06:06+00:00",
        )
        m2 = streams.StreamManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)

    def test_kind_defaults_to_reg(self):
        m = streams.StreamManifest(
            stream="s.zfs", snapshot="s", source="t",
            guid="g", checksum="c", size=1, created="now",
        )
        self.assertEqual(m.kind, "incremental")

    def test_base_snapshot_defaults_to_none(self):
        m = streams.StreamManifest(
            stream="s.zfs", snapshot="s", source="t",
            guid="g", checksum="c", size=1, created="now",
        )
        self.assertIsNone(m.base_snapshot)

    def test_to_dict_includes_kind(self):
        m = streams.StreamManifest(
            stream="s.zfs", snapshot="s", source="t",
            guid="g", checksum="c", size=1, created="now",
        )
        d = m.to_dict()
        self.assertIn("kind", d)

    def test_to_dict_includes_base_snapshot(self):
        m = streams.StreamManifest(
            stream="s.zfs", snapshot="s", source="t",
            guid="g", checksum="c", size=1, created="now",
        )
        d = m.to_dict()
        self.assertIn("base_snapshot", d)

    def test_from_dict_missing_kind_defaults(self):
        d = {
            "stream": "s.zfs", "snapshot": "s", "source": "t",
            "guid": "g", "checksum": "c", "size": 1, "created": "now",
        }
        m = streams.StreamManifest.from_dict(d)
        self.assertEqual(m.kind, "incremental")

    def test_from_dict_missing_base_snapshot_defaults(self):
        d = {
            "stream": "s.zfs", "snapshot": "s", "source": "t",
            "guid": "g", "checksum": "c", "size": 1, "created": "now",
        }
        m = streams.StreamManifest.from_dict(d)
        self.assertIsNone(m.base_snapshot)

    def test_from_dict_invalid_kind_raises(self):
        d = {
            "stream": "s.zfs", "snapshot": "s", "source": "t",
            "guid": "g", "checksum": "c", "size": 1, "created": "now",
            "kind": "invalid_kind",
        }
        with self.assertRaises(ValueError):
            streams.StreamManifest.from_dict(d)

    def test_roundtrip_reg(self):
        m1 = streams.StreamManifest(
            stream="s.zfs", snapshot="ts-reg", source="tank/a",
            guid="g", checksum="c", size=100, created="now",
            kind="incremental", base_snapshot="ts-mark",
        )
        m2 = streams.StreamManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)
        self.assertEqual(m2.kind, "incremental")
        self.assertEqual(m2.base_snapshot, "ts-mark")

    def test_roundtrip_rollup(self):
        m1 = streams.StreamManifest(
            stream="s.zfs", snapshot="ts-rollup", source="tank/a",
            guid="g", checksum="c", size=100, created="now",
            kind="rollup", base_snapshot="ts-mark",
        )
        m2 = streams.StreamManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)
        self.assertEqual(m2.kind, "rollup")

    def test_roundtrip_full(self):
        m1 = streams.StreamManifest(
            stream="s.zfs", snapshot="ts-full", source="tank/a",
            guid="g", checksum="c", size=100, created="now",
            kind="full", base_snapshot=None,
        )
        m2 = streams.StreamManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)
        self.assertEqual(m2.kind, "full")
        self.assertIsNone(m2.base_snapshot)


class TestManifestFilename(pilotest.TestCase):

    def test_reg(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.REG)
        self.assertEqual(
            streams.manifest_filename(snap),
            "20260522_010203_000000-reg.zfs.manifest",
        )

    def test_mark(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.MARK)
        self.assertEqual(
            streams.manifest_filename(snap),
            "20260522_010203_000000-mark.zfs.manifest",
        )


class TestManifestFilepath(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_manifest_filepath(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.REG)
        result = streams.manifest_filepath(snap)
        self.assertEqual(
            result,
            Path("/out/20260522/20260522_010203_000000-reg.zfs.manifest"),
        )


class TestWriteStreamManifest(pilotest.TestCase):

    def test_writes_sidecar(self):
        with pilotest.tmpdir() as td:
            out_root = td / 'streams'
            env = {"PILO_STREAM_OUTPUT_PATH": str(out_root)}
            out_root.mkdir(parents=True, exist_ok=True)
            date_dir = out_root / "20260522"
            date_dir.mkdir(parents=True, exist_ok=True)
            stream_path = date_dir / "20260522_010203_000000-reg.zfs"
            stream_path.write_bytes(b"hello world")

            with patch.dict(os.environ, env):
                result = streams.write_stream_manifest(
                    stream_path,
                    snapshot_name="20260522_010203_000000-reg",
                    source="tank/a",
                    guid="abcdef",
                )

                expected_manifest = stream_path.with_suffix(
                    ".zfs.manifest"
                )
                self.assertEqual(result, expected_manifest)
                self.assertTrue(expected_manifest.exists())

                m = streams.load_stream_manifest(expected_manifest)
        self.assertEqual(m.stream, "20260522/20260522_010203_000000-reg.zfs")
        self.assertEqual(m.snapshot, "20260522_010203_000000-reg")
        self.assertEqual(m.source, "tank/a")
        self.assertEqual(m.guid, "abcdef")
        self.assertIsInstance(m.size, int)
        self.assertGreater(m.size, 0)
        self.assertIn("2026", m.created)

    def test_checksum_matches_file_content(self):
        with pilotest.tmpdir() as td:
            out_root = td / 'streams'
            env = {"PILO_STREAM_OUTPUT_PATH": str(out_root)}
            date_dir = out_root / "20260522"
            date_dir.mkdir(parents=True, exist_ok=True)
            stream_path = date_dir / "20260522_010203_000000-reg.zfs"
            stream_path.write_bytes(b"hello world")

            import hashlib
            expected = hashlib.sha256(b"hello world").hexdigest()

            with patch.dict(os.environ, env):
                result_path = streams.write_stream_manifest(
                    stream_path,
                    snapshot_name="ts-reg",
                    source="tank/a",
                    guid="g",
                )
                m = streams.load_stream_manifest(result_path)
        self.assertEqual(m.checksum, expected)

    def test_size_matches_file(self):
        with pilotest.tmpdir() as td:
            out_root = td / 'streams'
            env = {"PILO_STREAM_OUTPUT_PATH": str(out_root)}
            date_dir = out_root / "20260522"
            date_dir.mkdir(parents=True, exist_ok=True)
            stream_path = date_dir / "20260522_010203_000000-reg.zfs"
            data = b"x" * 12345
            stream_path.write_bytes(data)

            with patch.dict(os.environ, env):
                result_path = streams.write_stream_manifest(
                    stream_path,
                    snapshot_name="ts-reg",
                    source="tank/a",
                    guid="g",
                )
                m = streams.load_stream_manifest(result_path)
        self.assertEqual(m.size, 12345)

    def test_nonexistent_file_raises(self):
        stream_path = Path("/tmp/nonexistent/stream.zfs")
        with self.assertRaises(FileNotFoundError):
            streams.write_stream_manifest(
                stream_path,
                snapshot_name="ts-reg",
                source="tank/a",
                guid="g",
            )


class TestWriteIncrementalManifest(pilotest.TestCase):

    def test_writes_incremental_kind(self):
        with pilotest.tmpdir() as td:
            out_root = td / 'streams'
            env = {"PILO_STREAM_OUTPUT_PATH": str(out_root)}
            out_root.mkdir(parents=True, exist_ok=True)
            date_dir = out_root / "20260522"
            date_dir.mkdir(parents=True, exist_ok=True)
            stream_path = date_dir / "stream.zfs"
            stream_path.write_bytes(b"data")

            with patch.dict(os.environ, env):
                result = streams.write_incremental_manifest(
                    stream_path, "ts-reg", "tank/a", "g",
                    base_snapshot="ts-mark",
                )
                m = streams.load_stream_manifest(result)
        self.assertEqual(m.kind, "incremental")
        self.assertEqual(m.base_snapshot, "ts-mark")


class TestWriteRollupManifest(pilotest.TestCase):

    def test_writes_rollup_kind(self):
        with pilotest.tmpdir() as td:
            out_root = td / 'streams'
            env = {"PILO_STREAM_OUTPUT_PATH": str(out_root)}
            out_root.mkdir(parents=True, exist_ok=True)
            date_dir = out_root / "20260522"
            date_dir.mkdir(parents=True, exist_ok=True)
            stream_path = date_dir / "stream.zfs"
            stream_path.write_bytes(b"data")

            with patch.dict(os.environ, env):
                result = streams.write_rollup_manifest(
                    stream_path, "ts-rollup", "tank/a", "g",
                    base_snapshot="ts-mark",
                )
                m = streams.load_stream_manifest(result)
        self.assertEqual(m.kind, "rollup")
        self.assertEqual(m.base_snapshot, "ts-mark")


class TestLoadStreamManifest(pilotest.TestCase):

    def test_load_valid(self):
        d = {
            "stream": "20260522/s.zfs",
            "snapshot": "ts-reg",
            "source": "tank/a",
            "guid": "abc",
            "checksum": "def",
            "size": 100,
            "created": "2026-01-01T00:00:00+00:00",
        }
        path = Path("/tmp/test_stream_manifest.json")
        try:
            path.write_text(__import__("json").dumps(d))
            m = streams.load_stream_manifest(path)
            self.assertEqual(m.stream, "20260522/s.zfs")
            self.assertEqual(m.size, 100)
        finally:
            path.unlink(missing_ok=True)

    def test_malformed_json_raises(self):
        path = Path("/tmp/test_bad_manifest.json")
        try:
            path.write_text("not json")
            with self.assertRaises(Exception):
                streams.load_stream_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            streams.load_stream_manifest(Path("/tmp/no_such_file.json"))


class TestVerifyOne(pilotest.TestCase):

    def _write_pair(self, td, data=b"hello world",
                    checksum=None, size=None):
        import hashlib
        stream_path = td / "s.zfs"
        stream_path.write_bytes(data)
        if checksum is None:
            checksum = hashlib.sha256(data).hexdigest()
        if size is None:
            size = len(data)
        manifest = {
            "stream": "s.zfs",
            "snapshot": "ts-reg",
            "source": "tank/a",
            "guid": "g",
            "checksum": checksum,
            "size": size,
            "created": "2026-01-01T00:00:00+00:00",
        }
        manifest_path = td / ("s" + streams.MANIFEST_SUFFIX)
        manifest_path.write_text(__import__("json").dumps(manifest))
        return stream_path, manifest_path

    def test_ok_manifest(self):
        with pilotest.tmpdir() as td:
            _, mpath = self._write_pair(td)
            status, msg = streams.verify_one(mpath)
            self.assertEqual(status, "OK")
            self.assertIn("s.zfs.manifest", msg)

    def test_mismatch_manifest(self):
        with pilotest.tmpdir() as td:
            self._write_pair(td, checksum="bad" * 20)
            mpath = td / ("s" + streams.MANIFEST_SUFFIX)
            status, msg = streams.verify_one(mpath)
            self.assertEqual(status, "MISMATCH")

    def test_missing_stream_for_manifest(self):
        with pilotest.tmpdir() as td:
            manifest = {
                "stream": "s.zfs",
                "snapshot": "ts-reg",
                "source": "tank/a",
                "guid": "g",
                "checksum": "c" * 64,
                "size": 0,
                "created": "2026-01-01T00:00:00+00:00",
            }
            mpath = td / ("s" + streams.MANIFEST_SUFFIX)
            mpath.write_text(__import__("json").dumps(manifest))
            status, msg = streams.verify_one(mpath)
            self.assertEqual(status, "NOT_FOUND")
            self.assertIn("s.zfs", msg)

    def test_malformed_manifest(self):
        with pilotest.tmpdir() as td:
            spath = td / "s.zfs"
            spath.write_bytes(b"data")
            mpath = td / ("s" + streams.MANIFEST_SUFFIX)
            mpath.write_text("not json")
            status, msg = streams.verify_one(mpath)
            self.assertEqual(status, "ERROR")

    def test_ok_zfs_with_manifest(self):
        with pilotest.tmpdir() as td:
            spath, _ = self._write_pair(td)
            status, msg = streams.verify_one(spath)
            self.assertEqual(status, "OK")

    def test_no_manifest_for_zfs(self):
        with pilotest.tmpdir() as td:
            spath = td / "s.zfs"
            spath.write_bytes(b"hello")
            status, msg = streams.verify_one(spath)
            self.assertEqual(status, "NO_MANIFEST")

    def test_not_found(self):
        status, msg = streams.verify_one(Path("/nonexistent/path"))
        self.assertEqual(status, "NOT_FOUND")

    def test_not_stream_file(self):
        with pilotest.tmpdir() as td:
            f = td / "readme.txt"
            f.write_text("hello")
            status, msg = streams.verify_one(f)
            self.assertEqual(status, "NOT_STREAM")
