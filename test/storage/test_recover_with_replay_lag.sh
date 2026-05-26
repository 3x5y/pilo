#!/bin/sh
set -e

# 1. seed replica with baseline snapshot
pilo storage-snapshot-mark
MARK=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
MARK=${MARK#*@}
pilo storage-replica-seed

# verify replica has the mark snapshot after seed
zfs list -Ho name "$PILO_SECONDARY_ROOTS"@$MARK >/dev/null

# 2. create incremental snapshots + export streams
pilo storage-snapshot-reg
INCR1=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR1=${INCR1#*@}
capture_status pilo storage-stream-export "$TEST_ROOT@$INCR1" "$TEST_ROOT@$MARK"
assert_command_ok
STREAM_DIR=$(dirname "$OUTPUT")

pilo storage-snapshot-reg
INCR2=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR2=${INCR2#*@}
capture_status pilo storage-stream-export "$TEST_ROOT@$INCR2" "$TEST_ROOT@$INCR1"
assert_command_ok

# 3. capture GUIDs of incremental snapshots before destruction
GUID1=$(zfs list -Ho guid -t snapshot "$TEST_ROOT@$INCR1")
GUID2=$(zfs list -Ho guid -t snapshot "$TEST_ROOT@$INCR2")

# 4. destroy primary (simulate loss) and recover with stream dir
clear_holds
zfs destroy -r "$TEST_ROOT"

capture_status pilo storage-recover "$TEST_ROOT" "$STREAM_DIR"
assert_command_ok

# 5. verify both incrementals replayed onto restored primary
zfs list -t snapshot -Ho name "$TEST_ROOT" | assert_grep "$INCR1"
zfs list -t snapshot -Ho name "$TEST_ROOT" | assert_grep "$INCR2"

# 6. verify GUIDs match — stream replay preserves snapshot GUIDs
GUID1_RESTORED=$(zfs list -Ho guid -t snapshot "$TEST_ROOT@$INCR1")
GUID2_RESTORED=$(zfs list -Ho guid -t snapshot "$TEST_ROOT@$INCR2")
[ "$GUID1_RESTORED" = "$GUID1" ] || fail "GUID mismatch for $INCR1"
[ "$GUID2_RESTORED" = "$GUID2" ] || fail "GUID mismatch for $INCR2"

# 7. verify replica is unchanged — baseline snapshot still present
zfs list -Ho name "$PILO_SECONDARY_ROOTS"@$MARK >/dev/null
