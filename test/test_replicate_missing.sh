#!/bin/sh
set -e

SRC=$TEST_ROOT
DST=$TEST_REPLICA

system-snapshot t0
system-replicate "$SRC" "$DST"
# destroy base snapshot on source → break incremental chain
zfs destroy "$SRC@t0"
system-snapshot t1

capture_status system-replicate "$SRC" "$DST"

assert_command_fail
echo "$OUTPUT" | assert_grep ERROR
