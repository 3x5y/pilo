#!/bin/sh
set -e

# Create canonical anchor snapshot and seed replica
pilo snapshot 20260101_000000_000000-anchor
pilo replica-seed

# Create first incremental snapshot
pilo snapshot-incr
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
INCR1=${latest_snap#*@}

# Export stream1 (incremental from anchor)
capture_status pilo stream-export "$TEST_ROOT@$INCR1" \
    "$TEST_ROOT@20260101_000000_000000-anchor"
assert_command_ok

# Create second incremental snapshot
pilo snapshot-incr
latest_snap=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
INCR2=${latest_snap#*@}

# Export stream2 (incremental from incr1)
capture_status pilo stream-export "$TEST_ROOT@$INCR2" "$TEST_ROOT@$INCR1"
assert_command_ok
STREAM2="$OUTPUT"

# Create directory with only incr2's stream (missing base incr1)
mkdir -p "$TMP/out-of-order"
cp "$STREAM2" "$TMP/out-of-order/"
cp "$STREAM2.manifest" "$TMP/out-of-order/"

# Replaying incr2 without incr1 should fail — zfs recv rejects
# incremental with missing base
capture_status pilo stream-replay-all "$TMP/out-of-order" "$TEST_REPLICA"
assert_command_fail
