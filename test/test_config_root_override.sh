#!/bin/sh
set -eu

oldpath=$INTAKE_PATH
init_system tank/test/alt
mkfile data file.txt
pilo capture $TMP/file.txt

assert_file_exists $INTAKE_PATH/file.txt
assert_not_exists $oldpath/file.txt
