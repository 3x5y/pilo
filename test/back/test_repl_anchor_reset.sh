#!/bin/sh
set -e

pilo snapshot-incr
pilo replica-seed

pilo snapshot t1
pilo replicate

pilo snapshot-incr
pilo replicate

capture_status pilo replication-verify
assert_command_ok expected valid chain after new anchor
