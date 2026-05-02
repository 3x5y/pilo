#!/bin/sh
set -eu

mkfile "hello" "file1"

capture_status pilo capture "$TMP/file1"

assert_command_ok
