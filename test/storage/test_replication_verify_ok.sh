#!/bin/sh
set -e

# initial snapshot + replication
pilo storage-snapshot t0
pilo storage-replica-seed

# new snapshot
pilo storage-snapshot t1
pilo storage-replicate

capture_status pilo storage-replication-verify

assert_command_ok replication continuity broken
