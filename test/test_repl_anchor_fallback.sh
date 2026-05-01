#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate

pilo-snapshot t1

capture_status pilo-replicate

assert_command_ok replication should still work without anchors
