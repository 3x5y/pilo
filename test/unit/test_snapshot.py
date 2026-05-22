import unittest
from unittest.mock import patch

from pilo import util
from pilo.back import snapshot
from pilo.back.snapshot import (
    SnapshotKind,
    SnapshotName,
    parse_snapshot_name,
    classify_snapshot,
    is_anchor_snapshot,
    is_incremental_snapshot,
    is_extra_snapshot,
    create_anchor_snapshot,
    create_incremental_snapshot,
    create_extra_snapshot,
)
import pilotest


class TestSnapshotPolicy(pilotest.TestCase):

    def test_policy_builds_name(self):
        policy = snapshot.SnapshotPolicy(prefix="r")

        name = policy.build_name("20240101_000000_000000")

        self.assertEqual(name, "r-20240101_000000_000000")

    def test_policy_no_timestamp_for_raw(self):
        policy = snapshot.SnapshotPolicy(prefix="x", raw=True)

        name = policy.build_name("TS")

        self.assertEqual(name, "x")

    @patch("pilo.util.snapshot_timestamp", return_value="TS")
    def test_policy_uses_timestamp(self, mock_ts):
        policy = snapshot.SnapshotPolicy(prefix="x")

        name = policy.build_name(util.snapshot_timestamp())

        self.assertEqual(name, "x-TS")

    @patch("pilo.zfs.snapshot")
    def test_creates_snapshot(self, mock_snap):
        policy = snapshot.SnapshotPolicy(prefix="r")

        snap = snapshot.create_snapshot_with_policy(policy, "tank/a", ts="TS")

        mock_snap.assert_called_once_with("r-TS", "tank/a")
        self.assertEqual(snap, "tank/a@r-TS")

    @patch("pilo.back.snapshot.create_snapshot_with_policy")
    def test_prefixed_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@r-TS"

        snap = snapshot.create_prefixed_snapshot("r", "tank/a")

        self.assertEqual(snap, "tank/a@r-TS")
        mock_create.assert_called_once()

    @patch("pilo.back.snapshot.create_snapshot_with_policy")
    def test_create_snapshot_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@foo"

        snap = snapshot.create_snapshot("foo", "tank/a")

        self.assertEqual(snap, "tank/a@foo")


class TestSnapshotKind(pilotest.TestCase):

    def test_enum_values(self):
        self.assertEqual(SnapshotKind.ANCHOR.value, "anchor")
        self.assertEqual(SnapshotKind.INCR.value, "incr")
        self.assertEqual(SnapshotKind.EXTRA.value, "extra")

    def test_from_string(self):
        self.assertIs(SnapshotKind("anchor"), SnapshotKind.ANCHOR)
        self.assertIs(SnapshotKind("incr"), SnapshotKind.INCR)
        self.assertIs(SnapshotKind("extra"), SnapshotKind.EXTRA)

    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            SnapshotKind("unknown")


class TestSnapshotName(pilotest.TestCase):

    def test_anchor_format(self):
        name = SnapshotName("20260522_012345_000000", SnapshotKind.ANCHOR)
        self.assertEqual(name.format(), "20260522_012345_000000-anchor")

    def test_incremental_format(self):
        name = SnapshotName("20260522_012345_000000", SnapshotKind.INCR)
        self.assertEqual(name.format(), "20260522_012345_000000-incr")

    def test_extra_format(self):
        name = SnapshotName("20260522_012345_000000", SnapshotKind.EXTRA, "mylabel")
        self.assertEqual(name.format(), "20260522_012345_000000-extra-mylabel")

    def test_extra_requires_label(self):
        SnapshotName("ts", SnapshotKind.EXTRA, "x")

    def test_frozen(self):
        name = SnapshotName("ts", SnapshotKind.ANCHOR)
        with self.assertRaises(AttributeError):
            name.timestamp = "other"


class TestParseSnapshotName(pilotest.TestCase):

    def test_parse_anchor(self):
        result = parse_snapshot_name("20260522_012345_000000-anchor")
        self.assertIsNotNone(result)
        self.assertEqual(result.timestamp, "20260522_012345_000000")
        self.assertIs(result.kind, SnapshotKind.ANCHOR)
        self.assertIsNone(result.label)

    def test_parse_incremental(self):
        result = parse_snapshot_name("20260522_012345_000000-incr")
        self.assertIsNotNone(result)
        self.assertEqual(result.timestamp, "20260522_012345_000000")
        self.assertIs(result.kind, SnapshotKind.INCR)
        self.assertIsNone(result.label)

    def test_parse_extra(self):
        result = parse_snapshot_name("20260522_012345_000000-extra-mylabel")
        self.assertIsNotNone(result)
        self.assertEqual(result.timestamp, "20260522_012345_000000")
        self.assertIs(result.kind, SnapshotKind.EXTRA)
        self.assertEqual(result.label, "mylabel")

    def test_parse_extra_label_with_hyphen(self):
        result = parse_snapshot_name("ts-extra-type-of-thing")
        self.assertIsNotNone(result)
        self.assertEqual(result.label, "type-of-thing")

    def test_parse_roundtrip(self):
        for orig in [
            SnapshotName("20260522_012345_000000", SnapshotKind.ANCHOR),
            SnapshotName("20260522_012345_000000", SnapshotKind.INCR),
            SnapshotName("20260522_012345_000000", SnapshotKind.EXTRA, "x"),
        ]:
            parsed = parse_snapshot_name(orig.format())
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed.format(), orig.format())

    def test_parse_empty_returns_none(self):
        self.assertIsNone(parse_snapshot_name(""))

    def test_parse_no_separator_returns_none(self):
        self.assertIsNone(parse_snapshot_name("t0"))
        self.assertIsNone(parse_snapshot_name("baseline"))

    def test_parse_unknown_kind_returns_none(self):
        self.assertIsNone(parse_snapshot_name("ts-bogus"))
        self.assertIsNone(parse_snapshot_name("ts-foo-bar"))

    def test_parse_old_prefix_format_returns_none(self):
        self.assertIsNone(parse_snapshot_name("r-20260522_000000"))

    def test_parse_extra_without_label_returns_none(self):
        self.assertIsNone(parse_snapshot_name("ts-extra"))

    def test_parse_anchor_with_label_returns_none(self):
        self.assertIsNone(parse_snapshot_name("ts-anchor-label"))

    def test_parse_incr_with_label_returns_none(self):
        self.assertIsNone(parse_snapshot_name("ts-incr-label"))


class TestClassifySnapshot(pilotest.TestCase):

    def test_classify_anchor(self):
        self.assertIs(classify_snapshot("ts-anchor"), SnapshotKind.ANCHOR)

    def test_classify_incremental(self):
        self.assertIs(classify_snapshot("ts-incr"), SnapshotKind.INCR)

    def test_classify_extra(self):
        self.assertIs(classify_snapshot("ts-extra-x"), SnapshotKind.EXTRA)

    def test_classify_unknown_returns_none(self):
        self.assertIsNone(classify_snapshot("t0"))
        self.assertIsNone(classify_snapshot(""))
        self.assertIsNone(classify_snapshot("r-ts"))


class TestClassificationHelpers(pilotest.TestCase):

    def test_is_anchor_snapshot(self):
        self.assertTrue(is_anchor_snapshot("ts-anchor"))
        self.assertFalse(is_anchor_snapshot("ts-incr"))
        self.assertFalse(is_anchor_snapshot("t0"))

    def test_is_incremental_snapshot(self):
        self.assertTrue(is_incremental_snapshot("ts-incr"))
        self.assertFalse(is_incremental_snapshot("ts-anchor"))
        self.assertFalse(is_incremental_snapshot("t0"))

    def test_is_extra_snapshot(self):
        self.assertTrue(is_extra_snapshot("ts-extra-x"))
        self.assertFalse(is_extra_snapshot("ts-anchor"))
        self.assertFalse(is_extra_snapshot("t0"))


class TestCreateSnapshotHelpers(pilotest.TestCase):

    @patch("pilo.zfs.snapshot")
    def test_create_anchor(self, mock_snap):
        result = create_anchor_snapshot("tank/a", ts="TS")
        self.assertEqual(result, "tank/a@TS-anchor")
        mock_snap.assert_called_once_with("TS-anchor", "tank/a")

    @patch("pilo.zfs.snapshot")
    def test_create_incremental(self, mock_snap):
        result = create_incremental_snapshot("tank/a", ts="TS")
        self.assertEqual(result, "tank/a@TS-incr")
        mock_snap.assert_called_once_with("TS-incr", "tank/a")

    @patch("pilo.zfs.snapshot")
    def test_create_extra(self, mock_snap):
        result = create_extra_snapshot("tank/a", "mylabel", ts="TS")
        self.assertEqual(result, "tank/a@TS-extra-mylabel")
        mock_snap.assert_called_once_with("TS-extra-mylabel", "tank/a")

    @patch("pilo.zfs.snapshot")
    @patch("pilo.util.snapshot_timestamp", return_value="AUTO")
    def test_create_anchor_auto_timestamp(self, mock_ts, mock_snap):
        result = create_anchor_snapshot("tank/a")
        self.assertEqual(result, "tank/a@AUTO-anchor")
        mock_snap.assert_called_once_with("AUTO-anchor", "tank/a")

    @patch("pilo.zfs.snapshot")
    def test_create_empty_dataset_fatal(self, mock_snap):
        with pilotest.assert_fatal(self):
            create_anchor_snapshot("")

    @patch("pilo.zfs.snapshot")
    def test_create_incremental_empty_dataset_fatal(self, mock_snap):
        with pilotest.assert_fatal(self):
            create_incremental_snapshot("")
