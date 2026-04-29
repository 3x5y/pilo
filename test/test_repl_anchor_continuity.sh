#!/bin/sh
set -e

system-anchor-create rotation
system-replicate

system-snapshot t1
system-replicate

capture_status system-replication-verify

assert_command_ok chain should remain valid
