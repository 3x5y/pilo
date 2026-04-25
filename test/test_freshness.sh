#!/bin/sh
set -e

DATASET=tank/data/active/pile

zfs create -p $DATASET 2>/dev/null || true

zfs snapshot $DATASET@test_snap

capture_status system-status

[ $STATUS -eq 0 ] || fail status returned nonzero
echo $OUTPUT | assert_grep snapshot
