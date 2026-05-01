#!/bin/sh
set -e

pilo-anchor-create rotation
pilo-replicate

pilo-snapshot t1
pilo-replicate

pilo-anchor-create rotation
pilo-replicate

capture_status pilo-replication-verify
assert_command_ok expected valid chain after new anchor
