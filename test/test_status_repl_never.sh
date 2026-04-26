#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly

zfs snapshot $SRC@t0

capture_status system-status replication
[ $STATUS -ne 0 ] || fail expected replication warning
echo "$OUTPUT" | assert_grep replication
