#!/bin/sh
set -eu


pilo storage-snapshot-mark
ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-mark$" | tail -1)
ANCHOR=${ANCHOR#*@}

pilo storage-replica-seed

pilo storage-snapshot-reg
INCR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-reg$" | tail -1)
INCR=${INCR#*@}

capture_status pilo storage-stream-export \
        "$TEST_ROOT@$INCR"  \
        "$TEST_ROOT@$ANCHOR"
assert_command_ok
STREAM="$OUTPUT"

assert_file_exists "$STREAM"
assert_file_exists "$STREAM.manifest"

capture_status pilo storage-stream-verify "$STREAM"
assert_command_ok

capture_status pilo storage-stream-replay "$STREAM" "$TEST_REPLICA"
assert_command_ok
echo "$OUTPUT" | assert_grep "APPLIED"

zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR"
