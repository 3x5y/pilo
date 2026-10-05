#!/bin/sh
set -e

file=bad.txt
archive=filing/2099
mkdir -p /$PILE/out/$archive
echo data > /$PILE/out/$archive/$file
create_pile_manifest

# dataset does NOT exist
capture_status pilo content-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "missing required dataset"
