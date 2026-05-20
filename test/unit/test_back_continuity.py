import unittest
from unittest.mock import patch, Mock

from pilo.back import continuity
from pilo.topology import SecondaryConfig
import pilotest


class TestContinuityAnchor(pilotest.TestCase):

    def setUp(self):
        self.cx = pilotest.make_context()
        self.cx.secondary_configs = [
            SecondaryConfig(label="pool1", root="pool1/backup"),
            SecondaryConfig(label="pool2", root="pool2/backup"),
        ]
        self.cx.root_dataset = "tank/a"


class TestHoldTag(TestContinuityAnchor):

    def test_hold_tag_format(self):
        self.assertEqual(continuity.hold_tag("z1"), "pilo:z1")

    def test_hold_tag_stable(self):
        self.assertEqual(
            continuity.hold_tag("z1"),
            continuity.hold_tag("z1"),
        )


class TestAnchors(TestContinuityAnchor):

    @patch("pilo.zfs.held_snapshots")
    def test_anchors_all_labels(self, mock_held):
        def side_effect(ds, tag=None):
            if tag == "pilo:pool1":
                return ["tank/a@snap1"]
            if tag == "pilo:pool2":
                return ["tank/a@snap2", "tank/a@snap3"]
            return []

        mock_held.side_effect = side_effect

        result = continuity.anchors(self.cx)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].secondary_label, "pool1")
        self.assertEqual(result[0].snapshot, "tank/a@snap1")
        self.assertEqual(result[1].secondary_label, "pool2")
        self.assertEqual(result[1].snapshot, "tank/a@snap2")
        self.assertEqual(result[2].secondary_label, "pool2")
        self.assertEqual(result[2].snapshot, "tank/a@snap3")

    @patch("pilo.zfs.held_snapshots")
    def test_anchors_filtered_by_label(self, mock_held):
        mock_held.return_value = ["tank/a@snap1"]

        result = continuity.anchors(self.cx, label="pool1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].secondary_label, "pool1")
        self.assertEqual(result[0].snapshot, "tank/a@snap1")
        mock_held.assert_called_once_with(
            self.cx.root_dataset,
            tag="pilo:pool1",
        )

    @patch("pilo.zfs.held_snapshots")
    def test_anchors_empty_when_no_holds(self, mock_held):
        mock_held.return_value = []

        result = continuity.anchors(self.cx)

        self.assertEqual(result, [])

    @patch("pilo.zfs.held_snapshots")
    def test_anchors_empty_when_no_secondary_configs(self, mock_held):
        self.cx.secondary_configs = []

        result = continuity.anchors(self.cx)

        self.assertEqual(result, [])
        mock_held.assert_not_called()


class TestLatestAnchor(TestContinuityAnchor):

    @patch("pilo.zfs.held_snapshots")
    def test_latest_anchor(self, mock_held):
        mock_held.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
            "tank/a@snap3",
        ]

        result = continuity.latest_anchor(self.cx, "pool1")

        self.assertIsNotNone(result)
        self.assertEqual(result.secondary_label, "pool1")
        self.assertEqual(result.snapshot, "tank/a@snap3")

    @patch("pilo.zfs.held_snapshots")
    def test_latest_anchor_none(self, mock_held):
        mock_held.return_value = []

        result = continuity.latest_anchor(self.cx, "pool1")

        self.assertIsNone(result)


class TestApplyReleaseHolds(TestContinuityAnchor):

    @patch("pilo.zfs.hold")
    def test_apply_hold(self, mock_hold):
        continuity.apply_hold(self.cx, "pool1", "tank/a@snap1")

        mock_hold.assert_called_once_with(
            "pilo:pool1",
            "tank/a@snap1",
        )

    @patch("pilo.zfs.release")
    def test_release_hold(self, mock_release):
        continuity.release_hold(self.cx, "pool2", "tank/a@snap2")

        mock_release.assert_called_once_with(
            "pilo:pool2",
            "tank/a@snap2",
        )


class TestUnheldSnapshots(TestContinuityAnchor):

    @patch("pilo.zfs.snapshots_userrefs")
    def test_none_held(self, mock_userrefs):
        mock_userrefs.return_value = [
            ("tank/a@snap1", 0),
            ("tank/a@snap2", 0),
            ("tank/a@snap3", 0),
        ]

        result = continuity.unheld_snapshots("tank/a")

        self.assertEqual(result, [
            "tank/a@snap1",
            "tank/a@snap2",
            "tank/a@snap3",
        ])

    @patch("pilo.zfs.snapshots_userrefs")
    def test_stops_at_first_held(self, mock_userrefs):
        mock_userrefs.return_value = [
            ("tank/a@snap1", 0),
            ("tank/a@snap2", 0),
            ("tank/a@snap3", 1),
            ("tank/a@snap4", 0),
        ]

        result = continuity.unheld_snapshots("tank/a")

        self.assertEqual(result, [
            "tank/a@snap1",
            "tank/a@snap2",
        ])

    @patch("pilo.zfs.snapshots_userrefs")
    def test_all_held(self, mock_userrefs):
        mock_userrefs.return_value = [
            ("tank/a@snap1", 2),
            ("tank/a@snap2", 1),
        ]

        result = continuity.unheld_snapshots("tank/a")

        self.assertEqual(result, [])

    @patch("pilo.zfs.snapshots_userrefs")
    def test_empty_dataset(self, mock_userrefs):
        mock_userrefs.return_value = []

        result = continuity.unheld_snapshots("tank/a")

        self.assertEqual(result, [])


class TestResolveLabel(TestContinuityAnchor):

    @patch("pilo.zfs.held_snapshots")
    def test_resolve_label_finds_anchor(self, mock_held):
        mock_held.return_value = ["pool1/backup@snap1", "pool1/backup@snap2"]

        result = continuity.resolve_label(self.cx, "pool1/backup")

        self.assertIsInstance(result, continuity.ContinuityAnchor)
        self.assertEqual(result.secondary_label, "pool1")
        self.assertEqual(result.snapshot, "pool1/backup@snap2")
        mock_held.assert_called_once_with(
            "pool1/backup",
            tag="pilo:pool1",
        )

    @patch("pilo.zfs.held_snapshots")
    def test_resolve_label_fatal_when_no_hold(self, mock_held):
        mock_held.return_value = []

        with pilotest.assert_fatal(self):
            continuity.resolve_label(self.cx, "pool1/backup")
