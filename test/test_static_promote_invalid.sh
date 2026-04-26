#!/bin/sh
set -e

echo x > /tmp/bad.txt
system-capture /tmp/bad.txt
system-ingest-pile

# deliberately DO NOT create dataset
capture_status system-static-promote bad.txt filing/2099

assert_command_fail "accepted non-existent dataset"
echo "$OUTPUT" | assert_grep "dataset does not exist"
