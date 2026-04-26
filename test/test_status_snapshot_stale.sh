#!/bin/sh
set -e

DATASET=tank/data/active/pile-readonly

zfs snapshot $DATASET@stale
sleep 2

export CONFIG_SNAPSHOT_MAX_AGE=1
capture_status system-status snapshot
[ $STATUS -ne 0 ] || fail status returned nonzero
echo "$OUTPUT" | assert_grep snapshot
