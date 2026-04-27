#!/bin/sh
set -e

FILE=file.txt

echo good > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-static-promote $FILE collection

# reintroduce conflicting version
echo bad > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

capture_status system-static-promote $FILE collection

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$FILE

# original must remain
assert_grep good < /tank/data/static/collection/$FILE
