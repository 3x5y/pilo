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
    def test_unset_env_raises_keyerror(self):
        with self.assertRaises(KeyError):
            streams.stream_output_path()


class TestStreamFilename(pilotest.TestCase):

    def test_incremental(self):
        self.assertEqual(
            streams.stream_filename("20260522_010203_000000", "incr"),
            "20260522_010203_000000-incr.zfs",
        )

    def test_anchor(self):
        self.assertEqual(
            streams.stream_filename("20260522_010203_000000", "anchor"),
            "20260522_010203_000000-anchor.zfs",
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
    def test_full_path_incremental(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.INCR)
        result = streams.stream_filepath(snap)
        self.assertEqual(
            result, Path("/out/20260522/20260522_010203_000000-incr.zfs")
        )

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_full_path_anchor(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.ANCHOR)
        result = streams.stream_filepath(snap)
        self.assertEqual(
            result, Path("/out/20260522/20260522_010203_000000-anchor.zfs")
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
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.INCR)
        result = streams.export_incremental_stream("tank/a", snap)

        expected_path = Path(
            "/out/20260522/20260522_010203_000000-incr.zfs"
        )
        self.assertEqual(result, expected_path)
        mock_send.assert_called_once_with(
            "tank/a@20260522_010203_000000-incr",
            expected_path,
        )
        mock_guid.assert_called_once_with(
            "tank/a@20260522_010203_000000-incr"
        )
        mock_manifest.assert_called_once_with(
            expected_path,
            "20260522_010203_000000-incr",
            "tank/a",
            "guid123",
        )

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.back.streams.zfs.get_guid", return_value="guid456")
    @patch("pilo.back.streams.zfs.send_incremental_to_file")
    def test_incremental_export_with_base(self, mock_send, mock_guid, mock_manifest):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.INCR)
        base = SnapshotName(
            "20260522_010000_000000", SnapshotKind.ANCHOR
        )
        result = streams.export_incremental_stream(
            "tank/a", snap, base=base,
        )

        expected_path = Path(
            "/out/20260522/20260522_010203_000000-incr.zfs"
        )
        self.assertEqual(result, expected_path)
        mock_send.assert_called_once_with(
            "tank/a@20260522_010000_000000-anchor",
            "tank/a@20260522_010203_000000-incr",
            expected_path,
        )
        mock_guid.assert_called_once_with(
            "tank/a@20260522_010203_000000-incr"
        )
        mock_manifest.assert_called_once_with(
            expected_path,
            "20260522_010203_000000-incr",
            "tank/a",
            "guid456",
        )


class TestStreamManifest(pilotest.TestCase):

    def test_manifest_fields(self):
        m = streams.StreamManifest(
            stream="20260522/20260522_010203_000000-incr.zfs",
            snapshot="20260522_010203_000000-incr",
            source="tank/a",
            guid="1234567890abcdef",
            checksum="abc" * 20,
            size=4096,
            created="2026-05-22T01:02:03.123456+00:00",
        )
        self.assertEqual(m.stream, "20260522/20260522_010203_000000-incr.zfs")
        self.assertEqual(m.size, 4096)

    def test_to_dict(self):
        m = streams.StreamManifest(
            stream="20260522/s.zfs",
            snapshot="ts-incr",
            source="tank/a",
            guid="guid",
            checksum="chk",
            size=100,
            created="2026-01-01T00:00:00+00:00",
        )
        d = m.to_dict()
        self.assertEqual(d["stream"], "20260522/s.zfs")
        self.assertEqual(d["size"], 100)
        self.assertEqual(d["snapshot"], "ts-incr")

    def test_from_dict(self):
        d = {
            "stream": "20260522/s.zfs",
            "snapshot": "ts-incr",
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
            snapshot="ts-incr",
            source="tank/a",
            guid="abc123",
            checksum="def456",
            size=777,
            created="2026-06-06T06:06:06+00:00",
        )
        m2 = streams.StreamManifest.from_dict(m1.to_dict())
        self.assertEqual(m1, m2)


class TestManifestFilename(pilotest.TestCase):

    def test_incremental(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.INCR)
        self.assertEqual(
            streams.manifest_filename(snap),
            "20260522_010203_000000-incr.zfs.manifest",
        )

    def test_anchor(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.ANCHOR)
        self.assertEqual(
            streams.manifest_filename(snap),
            "20260522_010203_000000-anchor.zfs.manifest",
        )


class TestManifestFilepath(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/out"})
    def test_manifest_filepath(self):
        snap = SnapshotName("20260522_010203_000000", SnapshotKind.INCR)
        result = streams.manifest_filepath(snap)
        self.assertEqual(
            result,
            Path("/out/20260522/20260522_010203_000000-incr.zfs.manifest"),
        )


class TestWriteStreamManifest(pilotest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/tmp/stream_out"})
    def test_writes_sidecar(self):
        out_root = Path("/tmp/stream_out")
        out_root.mkdir(parents=True, exist_ok=True)
        date_dir = out_root / "20260522"
        date_dir.mkdir(parents=True, exist_ok=True)
        stream_path = date_dir / "20260522_010203_000000-incr.zfs"
        stream_path.write_bytes(b"hello world")

        result = streams.write_stream_manifest(
            stream_path,
            snapshot_name="20260522_010203_000000-incr",
            source="tank/a",
            guid="abcdef",
        )

        expected_manifest = stream_path.with_suffix(
            ".zfs.manifest"
        )
        self.assertEqual(result, expected_manifest)
        self.assertTrue(expected_manifest.exists())

        m = streams.load_stream_manifest(expected_manifest)
        self.assertEqual(m.stream, "20260522/20260522_010203_000000-incr.zfs")
        self.assertEqual(m.snapshot, "20260522_010203_000000-incr")
        self.assertEqual(m.source, "tank/a")
        self.assertEqual(m.guid, "abcdef")
        self.assertIsInstance(m.size, int)
        self.assertGreater(m.size, 0)
        self.assertIn("2026", m.created)

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/tmp/stream_out2"})
    def test_checksum_matches_file_content(self):
        out_root = Path("/tmp/stream_out2")
        date_dir = out_root / "20260522"
        date_dir.mkdir(parents=True, exist_ok=True)
        stream_path = date_dir / "20260522_010203_000000-incr.zfs"
        stream_path.write_bytes(b"hello world")

        import hashlib
        expected = hashlib.sha256(b"hello world").hexdigest()

        result_path = streams.write_stream_manifest(
            stream_path,
            snapshot_name="ts-incr",
            source="tank/a",
            guid="g",
        )
        m = streams.load_stream_manifest(result_path)
        self.assertEqual(m.checksum, expected)

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/tmp/stream_out3"})
    def test_size_matches_file(self):
        out_root = Path("/tmp/stream_out3")
        date_dir = out_root / "20260522"
        date_dir.mkdir(parents=True, exist_ok=True)
        stream_path = date_dir / "20260522_010203_000000-incr.zfs"
        data = b"x" * 12345
        stream_path.write_bytes(data)

        result_path = streams.write_stream_manifest(
            stream_path,
            snapshot_name="ts-incr",
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
                snapshot_name="ts-incr",
                source="tank/a",
                guid="g",
            )


class TestLoadStreamManifest(pilotest.TestCase):

    def test_load_valid(self):
        d = {
            "stream": "20260522/s.zfs",
            "snapshot": "ts-incr",
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
            "snapshot": "ts-incr",
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
                "snapshot": "ts-incr",
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
