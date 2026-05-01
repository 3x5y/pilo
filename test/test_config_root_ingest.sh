#!/bin/sh
set -eu

oldpile=$PILE_PATH
init_system tank/test/alternate
mkfile data override.txt
capture_file override.txt
system-ingest-pile

assert_file_exists $PILE_PATH/in/override.txt
assert_not_exists $oldpile/in/override.txt
