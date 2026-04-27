#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

mkdir -p $INTAKE/foo
echo good > $INTAKE/foo/file.txt

system-ingest-pile

# conflicting re-upload
mkdir -p $INTAKE/foo
echo bad > $INTAKE/foo/file.txt

capture_status system-ingest-pile

assert_command_fail
echo "$OUTPUT" | assert_grep ERROR

assert_grep good < $PILE/in/foo/file.txt
assert_file_exists $INTAKE/foo/file.txt
