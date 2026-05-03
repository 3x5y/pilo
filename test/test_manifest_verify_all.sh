#!/bin/sh
set -eu

with_writable $COLLECTION \
    touch /"$COLLECTION"/a.txt

pilo manifest-update

# corrupt static file
with_writable $COLLECTION \
    sh -c "echo bad > /'$COLLECTION'/a.txt"

capture_status pilo manifest-verify
assert_command_fail
