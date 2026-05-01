#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate

pilo-snapshot t1
# DO NOT replicate t1

capture_status pilo-replication-verify

assert_command_fail expected replication lag
echo "$OUTPUT" | assert_grep "behind"
