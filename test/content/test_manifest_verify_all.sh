#!/bin/sh
set -eu


echo data > /$PILE/out/collection/file.txt
create_pile_manifest
pilo content-promote

# corrupt static file
with_writable $COLLECTION \
    sh -c "echo bad > /'$COLLECTION'/file.txt"

capture_status pilo manifest-verify
assert_command_fail
