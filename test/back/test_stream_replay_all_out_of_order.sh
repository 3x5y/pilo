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

# Create second incremental snapshot
pilo storage-snapshot-reg
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR2=${latest_snap#*@}

# Export stream2 (incremental from incr1)
capture_status pilo storage-stream-export "$TEST_ROOT@$INCR2" "$TEST_ROOT@$INCR1"
assert_command_ok
STREAM2="$OUTPUT"

# Create directory with only incr2's stream (missing base incr1)
mkdir -p "$TMP/out-of-order"
cp "$STREAM2" "$TMP/out-of-order/"
cp "$STREAM2.manifest" "$TMP/out-of-order/"

# Replaying incr2 without incr1 should fail — zfs recv rejects
# incremental with missing base
capture_status pilo storage-stream-replay-all "$TMP/out-of-order" "$TEST_REPLICA"
assert_command_fail
