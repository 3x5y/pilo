#!/bin/sh
set -e

# initial snapshot + replication
pilo snapshot t0
pilo replica-seed

# new snapshot
pilo snapshot t1
pilo replicate

capture_status pilo replication-verify

assert_command_ok replication continuity broken
