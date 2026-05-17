#!/bin/sh
set -e

pilo snapshot t0

capture_status pilo replication-verify

assert_command_fail expected failure without replication
echo "$OUTPUT" | assert_grep "STATUS=EMPTY"
