#!/bin/sh
set -e

# Create canonical anchor snapshot and seed replica
pilo storage-snapshot-mark
ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
ANCHOR=${ANCHOR#*@}
pilo storage-replica-seed

# Create first incremental snapshot
pilo storage-snapshot-reg
INCR1=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR1=${INCR1#*@}

# Export stream1 (incremental from anchor)
capture_status pilo storage-stream-export "$TEST_ROOT@$INCR1" \
    "$TEST_ROOT@$ANCHOR"
assert_command_ok
STREAM_DIR=$(dirname "$OUTPUT")

# Create second incremental snapshot
pilo storage-snapshot-reg
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR2=${latest_snap#*@}

# Export stream2 (incremental from incr1)
capture_status pilo storage-stream-export "$TEST_ROOT@$INCR2" "$TEST_ROOT@$INCR1"
assert_command_ok

# Replay all streams in date directory
capture_status pilo storage-stream-replay-all "$STREAM_DIR" "$TEST_REPLICA"
assert_command_ok

echo "$OUTPUT" | assert_grep "$INCR1"
echo "$OUTPUT" | assert_grep "$INCR2"

# Assert both snapshots exist on replica
zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR1"
zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR2"
