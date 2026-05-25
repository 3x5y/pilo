#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1
# DO NOT replicate t1

capture_status pilo storage-replication-verify

assert_command_fail expected replication lag
echo "$OUTPUT" | assert_grep "behind"
