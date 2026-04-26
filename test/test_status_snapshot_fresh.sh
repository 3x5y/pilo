#!/bin/sh
set -e

DATASET=tank/data/active/pile-readonly

zfs create -p $DATASET 2>/dev/null || true

zfs snapshot $DATASET@fresh

export CONFIG_SNAPSHOT_MAX_AGE=60
capture_status system-status snapshot
assert_command_ok status returned nonzero
echo "$OUTPUT" | assert_grep snapshot
