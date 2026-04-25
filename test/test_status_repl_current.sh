#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile

echo data > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t0

system-replicate

capture_status system-status replication
[ $STATUS -eq 0 ] || fail replication should be up to date
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep OK
