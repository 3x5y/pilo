#!/bin/sh
set -e

pilo-anchor-create rotation
pilo-replicate

pilo-snapshot t1
pilo-replicate

capture_status pilo-replication-verify

assert_command_ok chain should remain valid
