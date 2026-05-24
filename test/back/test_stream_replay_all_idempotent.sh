#!/bin/sh
set -e

# Create canonical anchor snapshot and seed replica
pilo snapshot 20260101_000000_000000-anchor
pilo replica-seed

# Create incremental snapshot
pilo snapshot-incr
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
INCR1=${latest_snap#*@}

# Export stream (incremental from anchor)
capture_status pilo stream-export "$TEST_ROOT@$INCR1" \
    "$TEST_ROOT@20260101_000000_000000-anchor"
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
