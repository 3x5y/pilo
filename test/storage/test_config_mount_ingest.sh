#!/bin/sh
set -eu

TEST_SKIP=1

mount=/alt-mount
oldpile=$PILO_PATH/pile
init_system tank/test/alt $mount
mkfile data override.txt
capture_file override.txt
pilo content-ingest

assert_file_exists $mount/pile/in/override.txt
assert_file_exists $PILO_PATH//pile/in/override.txt
assert_not_exists $oldpile/in/override.txt

