#!/bin/sh
set -eu

oldpath=$PILO_PATH/intake
init_system tank/test/alt /alt
mkfile data file.txt
capture_file file.txt

assert_file_exists /alt/intake/file.txt
assert_not_exists $oldpath/file.txt
