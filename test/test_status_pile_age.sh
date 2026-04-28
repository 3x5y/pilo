#!/bin/sh
set -e

file=old_file.txt
mkfile data $file
capture_file $file
touch -d '2 hours ago' /$INTAKE/$file
system-ingest-pile

export CONFIG_PILE_MAX_AGE=60
capture_status system-status pile

assert_command_fail status returned zero
echo "$OUTPUT" | assert_grep pile:
echo "$OUTPUT" | assert_grep old_file.txt
