#!/bin/sh
set -e

pilo snapshot fresh
pilo replica-seed

export CONFIG_SNAPSHOT_MAX_AGE=60 # redundant but explicit
capture_status pilo status snapshot

assert_command_ok status returned nonzero
echo "$OUTPUT" | assert_grep "lifecycle.state: NORMAL"
