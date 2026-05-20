#!/bin/sh
set -e

pilo snapshot-rpo
pilo replica-seed

pilo snapshot t1
pilo replicate

pilo snapshot-rpo
pilo replicate

capture_status pilo replication-verify
assert_command_ok expected valid chain after new anchor
