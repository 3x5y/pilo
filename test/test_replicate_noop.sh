#!/bin/sh
set -e

system-snapshot t0

system-replicate

capture_status system-replicate
assert_command_ok replication should be no-op
