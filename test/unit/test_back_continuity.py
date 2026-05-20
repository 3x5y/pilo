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


class TestExpiredSecondaryAnchors(TestContinuityAnchor):

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_holds")
    @patch("pilo.zfs.snapshots_userrefs")
    @patch("pilo.zfs.snapshot_guids")
    def test_some_expired(self, mock_guids, mock_userrefs, mock_holds, _):
        def guid_side_effect(ds):
            if ds == "tank/a":
                return [["tank/a@c", "333"]]
            return [
                ["pool1/backup@a", "111"],
                ["pool1/backup@b", "222"],
                ["pool1/backup@c", "333"],
                ["pool1/backup@d", "444"],
            ]

        mock_guids.side_effect = guid_side_effect
        mock_userrefs.return_value = [
            ("pool1/backup@a", 1),
            ("pool1/backup@b", 1),
            ("pool1/backup@c", 1),
            ("pool1/backup@d", 1),
        ]

        def holds_side_effect(snap):
            if "a" in snap:
                return [("pool1/backup@a", "pilo:pool1")]
            if "b" in snap:
                return [("pool1/backup@b", "pilo:pool1")]
            return []

        mock_holds.side_effect = holds_side_effect

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].secondary_label, "pool1")
        self.assertEqual(result[0].snapshot, "pool1/backup@a")
        self.assertEqual(result[1].secondary_label, "pool1")
        self.assertEqual(result[1].snapshot, "pool1/backup@b")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_holds")
    @patch("pilo.zfs.snapshots_userrefs")
    @patch("pilo.zfs.snapshot_guids")
    def test_stops_at_match(self, mock_guids, mock_userrefs, mock_holds, _):
        def guid_side_effect(ds):
            if ds == "tank/a":
                return [["tank/a@b", "222"]]
            return [
                ["pool1/backup@a", "111"],
                ["pool1/backup@b", "222"],
                ["pool1/backup@c", "333"],
            ]

        mock_guids.side_effect = guid_side_effect
        mock_userrefs.return_value = [
            ("pool1/backup@a", 1),
            ("pool1/backup@b", 1),
            ("pool1/backup@c", 1),
        ]

        def holds_side_effect(snap):
            return [(snap, "pilo:pool1")]

        mock_holds.side_effect = holds_side_effect

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].snapshot, "pool1/backup@a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_holds")
    @patch("pilo.zfs.snapshots_userrefs")
    @patch("pilo.zfs.snapshot_guids")
    def test_all_current(self, mock_guids, mock_userrefs, mock_holds, _):
        def guid_side_effect(ds):
            if ds == "tank/a":
                return [["tank/a@a", "111"], ["tank/a@b", "222"]]
            return [
                ["pool1/backup@a", "111"],
                ["pool1/backup@b", "222"],
            ]

        mock_guids.side_effect = guid_side_effect
        mock_userrefs.return_value = [
            ("pool1/backup@a", 1),
            ("pool1/backup@b", 1),
        ]
        mock_holds.return_value = []

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(result, [])

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_holds")
    @patch("pilo.zfs.snapshots_userrefs")
    @patch("pilo.zfs.snapshot_guids")
    def test_none_match_all_expired(self, mock_guids, mock_userrefs, mock_holds, _):
        def guid_side_effect(ds):
            if ds == "tank/a":
                return [["tank/a@x", "999"]]
            return [
                ["pool1/backup@a", "111"],
                ["pool1/backup@b", "222"],
            ]

        mock_guids.side_effect = guid_side_effect
        mock_userrefs.return_value = [
            ("pool1/backup@a", 1),
            ("pool1/backup@b", 1),
        ]

        def holds_side_effect(snap):
            return [(snap, "pilo:pool1")]

        mock_holds.side_effect = holds_side_effect

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(len(result), 2)

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_holds")
    @patch("pilo.zfs.snapshots_userrefs")
    @patch("pilo.zfs.snapshot_guids")
    def test_skips_unheld(self, mock_guids, mock_userrefs, mock_holds, _):
        def guid_side_effect(ds):
            if ds == "tank/a":
                return [["tank/a@c", "333"]]
            return [
                ["pool1/backup@a", "111"],
                ["pool1/backup@b", "222"],
                ["pool1/backup@c", "333"],
            ]

        mock_guids.side_effect = guid_side_effect
        mock_userrefs.return_value = [
            ("pool1/backup@a", 0),
            ("pool1/backup@b", 1),
            ("pool1/backup@c", 1),
        ]

        def holds_side_effect(snap):
            return [(snap, "pilo:pool1")]

        mock_holds.side_effect = holds_side_effect

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].snapshot, "pool1/backup@b")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.snapshot_guids")
    def test_empty_secondary(self, mock_guids, _):
        mock_guids.return_value = []

        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

        self.assertEqual(result, [])

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_secondary_not_exist(self, _):
        result = continuity.expired_secondary_anchors(
            self.cx, "pool1/backup",
        )

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


class TestPrimaryHoldsToRelease(TestContinuityAnchor):

    @patch("pilo.zfs.held_snapshots")
    def test_keep_one(self, mock_held):
        mock_held.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
            "tank/a@snap3",
            "tank/a@snap4",
            "tank/a@snap5",
        ]

        result = continuity.primary_holds_to_release(
            self.cx, "pool1/backup", keep=1,
        )

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].snapshot, "tank/a@snap1")
        self.assertEqual(result[1].snapshot, "tank/a@snap2")
        self.assertEqual(result[2].snapshot, "tank/a@snap3")
        self.assertEqual(result[3].snapshot, "tank/a@snap4")

    @patch("pilo.zfs.held_snapshots")
    def test_keep_three(self, mock_held):
        mock_held.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
            "tank/a@snap3",
            "tank/a@snap4",
            "tank/a@snap5",
        ]

        result = continuity.primary_holds_to_release(
            self.cx, "pool1/backup", keep=3,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].snapshot, "tank/a@snap1")
        self.assertEqual(result[1].snapshot, "tank/a@snap2")

    @patch("pilo.zfs.held_snapshots")
    def test_single_anchor_keep_one(self, mock_held):
        mock_held.return_value = ["tank/a@snap1"]

        result = continuity.primary_holds_to_release(
            self.cx, "pool1/backup", keep=1,
        )

        self.assertEqual(result, [])

    @patch("pilo.zfs.held_snapshots")
    def test_no_anchors(self, mock_held):
        mock_held.return_value = []

        result = continuity.primary_holds_to_release(
            self.cx, "pool1/backup", keep=1,
        )

        self.assertEqual(result, [])

    @patch("pilo.zfs.held_snapshots")
    def test_keep_exceeds_count(self, mock_held):
        mock_held.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
        ]

        result = continuity.primary_holds_to_release(
            self.cx, "pool1/backup", keep=5,
        )

        self.assertEqual(result, [])


class TestAgeingPlan(TestContinuityAnchor):

    @patch("pilo.back.continuity.primary_holds_to_release")
    @patch("pilo.back.continuity.expired_secondary_anchors")
    @patch("pilo.back.continuity.unheld_snapshots")
    def test_composes_correctly(self, mock_unheld, mock_expired, mock_primary):
        mock_unheld.side_effect = [
            ["sec@a", "sec@b"],
            ["pri@x"],
        ]
        mock_expired.return_value = [
            continuity.ContinuityAnchor(
                secondary_label="pool1", snapshot="sec@b",
            ),
        ]
        mock_primary.return_value = [
            continuity.ContinuityAnchor(
                secondary_label="pool1", snapshot="pri@a",
            ),
        ]

        plan = continuity.ageing_plan(self.cx, "pool1/backup", keep=1)

        self.assertIsInstance(plan, continuity.AgeingPlan)
        self.assertEqual(plan.secondary_to_prune, ["sec@a", "sec@b"])
        self.assertEqual(len(plan.secondary_to_release), 1)
        self.assertEqual(plan.secondary_to_release[0].snapshot, "sec@b")
        self.assertEqual(plan.primary_to_prune, ["pri@x"])
        self.assertEqual(len(plan.primary_to_release), 1)
        self.assertEqual(plan.primary_to_release[0].snapshot, "pri@a")

    @patch("pilo.back.continuity.primary_holds_to_release")
    @patch("pilo.back.continuity.expired_secondary_anchors")
    @patch("pilo.back.continuity.unheld_snapshots")
    def test_empty_plan(self, mock_unheld, mock_expired, mock_primary):
        mock_unheld.return_value = []
        mock_expired.return_value = []
        mock_primary.return_value = []

        plan = continuity.ageing_plan(self.cx, "pool1/backup")

        self.assertEqual(plan.secondary_to_prune, [])
        self.assertEqual(plan.secondary_to_release, [])
        self.assertEqual(plan.primary_to_prune, [])
        self.assertEqual(plan.primary_to_release, [])

    @patch("pilo.back.continuity.primary_holds_to_release")
    @patch("pilo.back.continuity.expired_secondary_anchors")
    @patch("pilo.back.continuity.unheld_snapshots")
    def test_keep_forwarded(self, mock_unheld, mock_expired, mock_primary):
        mock_unheld.return_value = []
        mock_expired.return_value = []
        mock_primary.return_value = []

        continuity.ageing_plan(self.cx, "pool1/backup", keep=3)

        mock_primary.assert_called_once_with(
            self.cx, "pool1/backup", keep=3,
        )

    def test_keep_below_one_fatal(self):
        with pilotest.assert_fatal(self):
            continuity.ageing_plan(self.cx, "pool1/backup", keep=0)

    def test_keep_negative_fatal(self):
        with pilotest.assert_fatal(self):
            continuity.ageing_plan(self.cx, "pool1/backup", keep=-1)


class TestAgeingPlanPreview(TestContinuityAnchor):

    def test_preview_empty_plan(self):
        plan = continuity.AgeingPlan(
            secondary_to_prune=[],
            secondary_to_release=[],
            primary_to_prune=[],
            primary_to_release=[],
        )
        lines = continuity.preview_ageing_plan(plan)
        self.assertEqual(lines, [])

    def test_preview_full_plan(self):
        plan = continuity.AgeingPlan(
            secondary_to_prune=["sec@a"],
            secondary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="pool1", snapshot="sec@b",
                ),
            ],
            primary_to_prune=["pri@x"],
            primary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="pool1", snapshot="pri@y",
                ),
            ],
        )
        lines = continuity.preview_ageing_plan(plan)
        self.assertEqual(lines, [
            "destroy sec@a",
            "release pilo:pool1 sec@b",
            "destroy pri@x",
            "release pilo:pool1 pri@y",
        ])

    def test_preview_secondary_to_prune_only(self):
        plan = continuity.AgeingPlan(
            secondary_to_prune=["sec@a", "sec@b"],
            secondary_to_release=[],
            primary_to_prune=[],
            primary_to_release=[],
        )
        lines = continuity.preview_ageing_plan(plan)
        self.assertEqual(lines, [
            "destroy sec@a",
            "destroy sec@b",
        ])

    def test_preview_primary_to_release_only(self):
        plan = continuity.AgeingPlan(
            secondary_to_prune=[],
            secondary_to_release=[],
            primary_to_prune=[],
            primary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="pool1", snapshot="pri@z",
                ),
            ],
        )
        lines = continuity.preview_ageing_plan(plan)
        self.assertEqual(lines, [
            "release pilo:pool1 pri@z",
        ])

    def test_preview_release_tag_matches_hold_tag(self):
        plan = continuity.AgeingPlan(
            secondary_to_prune=[],
            secondary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="my-label", snapshot="sec@x",
                ),
            ],
            primary_to_prune=[],
            primary_to_release=[],
        )
        lines = continuity.preview_ageing_plan(plan)
        self.assertEqual(lines[0],
                         "release pilo:my-label sec@x")

    def test_is_preview_mode_true(self):
        self.cx.args = ["--preview"]
        self.assertTrue(continuity.is_preview_mode(self.cx))

    def test_is_preview_mode_false_no_args(self):
        self.cx.args = []
        self.assertFalse(continuity.is_preview_mode(self.cx))

    def test_is_preview_mode_false_other_args(self):
        self.cx.args = ["--delete", "x"]
        self.assertFalse(continuity.is_preview_mode(self.cx))


class TestExecuteAgeingPlan(TestContinuityAnchor):

    def setUp(self):
        super().setUp()
        self.plan = continuity.AgeingPlan(
            secondary_to_prune=["pool1/backup@sec_a"],
            secondary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="pool1", snapshot="pool1/backup@sec_b",
                ),
            ],
            primary_to_prune=["tank/a@pri_a"],
            primary_to_release=[
                continuity.ContinuityAnchor(
                    secondary_label="pool1", snapshot="tank/a@pri_b",
                ),
            ],
        )

    @patch("pilo.back.continuity.zfs.release")
    @patch("pilo.back.continuity.zfs.destroy_snapshots")
    def test_execute_secondary_prune_first(self, mock_destroy, mock_release):
        continuity.execute_ageing_plan(self.cx, "pool1/backup", self.plan)

        self.assertEqual(mock_destroy.call_args_list[0][0][0],
                         ["pool1/backup@sec_a"])

    @patch("pilo.back.continuity.zfs.release")
    @patch("pilo.back.continuity.zfs.destroy_snapshots")
    def test_execute_releases_secondary_holds(self, mock_destroy, mock_release):
        continuity.execute_ageing_plan(self.cx, "pool1/backup", self.plan)

        mock_release.assert_any_call("pilo:pool1", "pool1/backup@sec_b")
        mock_release.assert_any_call("pilo:pool1", "tank/a@pri_b")

    @patch("pilo.back.continuity.zfs.release")
    @patch("pilo.back.continuity.zfs.destroy_snapshots")
    def test_execute_full_order(self, mock_destroy, mock_release):
        continuity.execute_ageing_plan(self.cx, "pool1/backup", self.plan)

        self.assertEqual(mock_destroy.call_args_list[0][0][0],
                         ["pool1/backup@sec_a"])
        self.assertEqual(mock_release.call_args_list[0][0],
                         ("pilo:pool1", "pool1/backup@sec_b"))
        self.assertEqual(mock_destroy.call_args_list[1][0][0],
                         ["tank/a@pri_a"])
        self.assertEqual(mock_release.call_args_list[1][0],
                         ("pilo:pool1", "tank/a@pri_b"))

    @patch("pilo.back.continuity.zfs.release")
    @patch("pilo.back.continuity.zfs.run")
    def test_execute_empty_plan(self, mock_run, mock_release):
        empty = continuity.AgeingPlan(
            secondary_to_prune=[],
            secondary_to_release=[],
            primary_to_prune=[],
            primary_to_release=[],
        )

        continuity.execute_ageing_plan(self.cx, "pool1/backup", empty)

        mock_run.assert_not_called()
        mock_release.assert_not_called()
