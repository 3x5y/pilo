#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
system-ingest-pile

capture_status system-status pile

assert_command_ok expected no pile age warning
