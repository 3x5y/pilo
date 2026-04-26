#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

echo data > $PILE/test.txt

# deliberately DO NOT create dataset
capture_status system-static-promote test.txt filing/2099

assert_command_fail "accepted non-existent dataset"
echo "$OUTPUT" | assert_grep "dataset does not exist"
