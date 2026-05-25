#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

# create replica-local orphan dataset
zfs create $TEST_REPLICA/orphan
zfs snapshot $TEST_REPLICA/orphan@archive

capture_status pilo storage-replication-verify

assert_command_ok orphan historical dataset should be tolerated
echo "$OUTPUT" | assert_grep "STATUS=OK"
