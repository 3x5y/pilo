#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

clear_holds $TEST_REPLICA/active/admin
zfs destroy $TEST_REPLICA/active/admin@t0

capture_status pilo replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
