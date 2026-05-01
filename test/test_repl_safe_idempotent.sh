#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

capture_status pilo replicate-safe

assert_command_ok expected no-op
