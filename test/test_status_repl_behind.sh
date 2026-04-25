#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile

# initial snapshot + replication
echo v1 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t0
system-replicate

capture_status system-status replication

# new snapshot, NOT replicated
echo v2 > /tank/data/active/pile/file.txt
zfs snapshot $SRC@t1

capture_status system-status replication
[ $STATUS -ne 0 ] || fail expected replication drift
echo "$OUTPUT" | assert_grep replication
echo "$OUTPUT" | assert_grep t1
