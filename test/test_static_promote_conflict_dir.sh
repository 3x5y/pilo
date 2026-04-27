#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
FILE=file.txt

with_writable $PILE \
    mkdir -p /$PILE/out/collection/x

echo good > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection/x
system-static-promote

# reintroduce conflicting version
echo bad > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection/x

capture_status system-static-promote

assert_command_fail expected conflict
echo "$OUTPUT" | assert_grep ERROR.*conflict.*$FILE

# original must remain
assert_grep good < /tank/data/static/collection/x/$FILE

