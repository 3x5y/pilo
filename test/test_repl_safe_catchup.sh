#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate

pilo-snapshot t1

capture_status pilo-replicate-safe

assert_command_ok expected catch-up replication
