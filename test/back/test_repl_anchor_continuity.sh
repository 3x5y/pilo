#!/bin/sh
set -e

pilo snapshot-rpo
pilo replica-seed

pilo snapshot t1
pilo replicate

capture_status pilo replication-verify

assert_command_ok chain should remain valid
