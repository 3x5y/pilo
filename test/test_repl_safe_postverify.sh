#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1

system-replicate-safe >/dev/null

capture_status system-replication-verify
assert_command_ok expected system to be consistent after safe replication
