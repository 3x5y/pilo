#!/bin/sh
set -eu

mount=/alt-mount
oldpile=$PILE_PATH
reset_system tank/test/alt $mount
mkfile data override.txt
capture_file override.txt
pilo ingest-pile

assert_file_exists $mount/active/pile-readonly/in/override.txt
assert_file_exists $PILE_PATH/in/override.txt
assert_not_exists $oldpile/in/override.txt

