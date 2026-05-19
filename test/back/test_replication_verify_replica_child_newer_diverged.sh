#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

# replica-local divergent child history
zfs snapshot $TEST_REPLICA/active/admin@evil

capture_status pilo replication-verify

assert_command_fail
echo "$OUTPUT" | assert_grep DIVERGED
