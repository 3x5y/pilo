#!/bin/sh
set -e

pilo storage-snapshot t0

capture_status pilo storage-replication-verify

assert_command_fail expected failure without replication
echo "$OUTPUT" | assert_grep "^ERROR: replica is uninitialized"
