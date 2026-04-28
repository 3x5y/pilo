#!/bin/sh
set -e

system-snapshot t0

capture_status system-replication-verify

assert_command_fail expected failure without replication
echo "$OUTPUT" | assert_grep "no snapshots"
