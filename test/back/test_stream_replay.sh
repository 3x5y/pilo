#!/bin/sh
set -eu


ANCHOR=20260101_000000_000000-anchor
INCR=20260101_123456_000000-incr

pilo snapshot $ANCHOR
pilo replica-seed

pilo snapshot $INCR

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
