#!/bin/sh
set -e

# Create anchor and seed
pilo storage-snapshot-mark
ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
ANCHOR=${ANCHOR#*@}
pilo storage-replica-seed

# Create an incremental snapshot and export it
pilo storage-snapshot-reg
INCR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR=${INCR#*@}

capture_status pilo storage-stream-export "$TEST_ROOT@$INCR" "$TEST_ROOT@$ANCHOR"
assert_command_ok

# Replay from $PILO_STREAM_OUTPUT_PATH root — discovers stream in date subdir
capture_status pilo storage-stream-replay-all "$PILO_STREAM_OUTPUT_PATH" "$TEST_REPLICA"
assert_command_ok
echo "$OUTPUT" | assert_grep "$INCR"

zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR"
