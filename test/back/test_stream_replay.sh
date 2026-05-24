#!/bin/sh
set -eu


pilo snapshot-anchor
ANCHOR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-anchor$" | tail -1)
ANCHOR=${ANCHOR#*@}

pilo replica-seed

pilo snapshot-incr
INCR=$(zfs list -t snapshot -r -Ho name -s creation \
    "$PILO_PRIMARY_ROOT" | grep -- "-incr$" | tail -1)
INCR=${INCR#*@}

capture_status pilo stream-export \
        "$TEST_ROOT@$INCR"  \
        "$TEST_ROOT@$ANCHOR"
assert_command_ok
STREAM="$OUTPUT"

assert_file_exists "$STREAM"
assert_file_exists "$STREAM.manifest"

capture_status pilo stream-verify "$STREAM"
assert_command_ok

capture_status pilo stream-replay "$STREAM" "$TEST_REPLICA"
assert_command_ok
echo "$OUTPUT" | assert_grep "APPLIED"

zfs list -t snapshot -Ho name "$TEST_REPLICA" | assert_grep "$INCR"
