#!/bin/sh
set -e

snap=t0

pilo storage-snapshot t0
pilo storage-replica-seed

capture_status pilo status replication

assert_command_ok replication should be up to date
echo "$OUTPUT" | assert_grep "lifecycle.state: NORMAL"
