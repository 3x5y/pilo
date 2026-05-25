#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

# source prunes old snapshot
clear_holds
zfs destroy $TEST_ROOT@t0

# replica still retains historical snapshot
zfs list -t snapshot | assert_grep "$TEST_REPLICA@t0"

capture_status pilo storage-replication-verify

assert_command_ok expected valid continuity
echo "$OUTPUT" | assert_grep "STATUS=OK"
