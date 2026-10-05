#!/bin/sh
set -e

capture_status pilo content-promote

assert_command_fail expected missing source failure
echo "$OUTPUT" | assert_grep "/out/ directory empty"
