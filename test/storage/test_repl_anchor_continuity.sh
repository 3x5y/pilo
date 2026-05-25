#!/bin/sh
set -e

pilo storage-snapshot-reg
pilo storage-replica-seed

pilo storage-snapshot t1
pilo storage-replicate

capture_status pilo storage-replication-verify

assert_command_ok chain should remain valid
