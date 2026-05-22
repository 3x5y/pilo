import os
import unittest
from pathlib import Path
from unittest.mock import patch

from pilo.back import streams
from pilo.back.snapshot import SnapshotKind, SnapshotName


class TestStreamOutputPath(unittest.TestCase):

    @patch.dict(os.environ, {"PILO_STREAM_OUTPUT_PATH": "/some/streams"})
    def test_reads_env(self):
        self.assertEqual(streams.stream_output_path(), Path("/some/streams"))

    @patch.dict(os.environ, {}, clear=True)
    def test_unset_env_raises_keyerror(self):
        with self.assertRaises(KeyError):
            streams.stream_output_path()


class TestStreamFilename(unittest.TestCase):

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


class TestStreamDateDir(unittest.TestCase):

    def test_extracts_first_eight_chars(self):
        self.assertEqual(
            streams.stream_date_dir("20260522_010203_000000"), "20260522"
        )

    def test_pads_short_string(self):
        self.assertEqual(streams.stream_date_dir("abc"), "abc")


class TestStreamFilepath(unittest.TestCase):

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
