#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1

capture_status system-replicate

assert_command_ok replication should still work without anchors
