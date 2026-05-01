#!/bin/sh
set -e

pilo snapshot t0

pilo replicate

capture_status pilo replicate
assert_command_ok replication should be no-op
