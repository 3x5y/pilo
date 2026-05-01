#!/bin/sh
set -e

pilo snapshot t0
pilo replicate
pilo replicate

capture_status pilo replication-verify

assert_command_ok replication should remain valid
