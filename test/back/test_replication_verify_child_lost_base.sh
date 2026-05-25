#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

clear_holds $TEST_REPLICA/active/admin
zfs destroy $TEST_REPLICA/active/admin@t0

capture_status pilo storage-replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
