#!/bin/sh
set -e

snap=t0

pilo snapshot t0
pilo replica-seed

capture_status pilo status replication

assert_command_ok replication should be up to date
echo "$OUTPUT" | assert_grep "lifecycle: NORMAL"
