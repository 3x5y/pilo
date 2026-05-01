#!/bin/sh
set -e

mkfile data file.txt
capture_file file.txt
pilo-ingest-pile

capture_status pilo-status pile

assert_command_ok expected no pile age warning
