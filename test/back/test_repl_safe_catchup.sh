#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

pilo storage-snapshot t1

capture_status pilo storage-replicate-safe

assert_command_ok expected catch-up replication
