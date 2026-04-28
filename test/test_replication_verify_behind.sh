#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1
# DO NOT replicate t1

capture_status system-replication-verify

assert_command_fail expected replication lag
echo "$OUTPUT" | assert_grep "behind"
