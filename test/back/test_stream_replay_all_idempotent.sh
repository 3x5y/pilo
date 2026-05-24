#!/bin/sh
set -e

# Create canonical anchor snapshot and seed replica
pilo snapshot-anchor
ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-anchor$" | tail -1)
ANCHOR=${ANCHOR#*@}
pilo replica-seed

# Create incremental snapshot
pilo snapshot-incr
INCR1=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
INCR1=${INCR1#*@}

# Export stream (incremental from anchor)
capture_status pilo stream-export "$TEST_ROOT@$INCR1" \
    "$TEST_ROOT@$ANCHOR"
assert_command_ok
STREAM_DIR=$(dirname "$OUTPUT")

# First replay
capture_status pilo stream-replay-all "$STREAM_DIR" "$TEST_REPLICA"
assert_command_ok
echo "$OUTPUT" | assert_grep "$INCR1"

# Second replay — same stream, idempotent
capture_status pilo stream-replay-all "$STREAM_DIR" "$TEST_REPLICA"
assert_command_ok
echo "$OUTPUT" | assert_grep "$INCR1"

# Snapshot exists on replica
zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR1"
