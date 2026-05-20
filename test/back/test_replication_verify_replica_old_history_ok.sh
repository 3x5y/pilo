#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

pilo snapshot t1
pilo replicate

# source prunes old snapshot
clear_holds
zfs destroy $TEST_ROOT@t0

# replica still retains historical snapshot
zfs list -t snapshot | assert_grep "$TEST_REPLICA@t0"

capture_status pilo replication-verify

assert_command_ok expected valid continuity
echo "$OUTPUT" | assert_grep "STATUS=OK"
