#!/bin/sh
set -e

file=bad-checksum.txt
echo good > /$PILE/out/collection/$file
create_pile_manifest

# source changes after the pile manifest was written
echo changed > /$PILE/out/collection/$file

capture_status pilo content-promote

assert_command_fail "promote should fail checksum verification"
echo "$OUTPUT" | assert_grep "checksum verification failed"

# planning failed: nothing was mutated
assert_file_exists /$PILE/out/collection/$file
assert_not_exists /$STATIC/collection/$file