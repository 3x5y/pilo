#!/bin/sh
set -e

system-anchor-create rotation
system-replicate

system-snapshot t1
system-replicate

system-anchor-create rotation
system-replicate

capture_status system-replication-verify
assert_command_ok expected valid chain after new anchor
