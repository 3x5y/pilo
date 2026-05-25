#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

# replica-local divergent child history
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo storage-replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
