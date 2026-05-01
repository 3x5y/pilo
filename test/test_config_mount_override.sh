#!/bin/sh
set -eu

oldpath=$INTAKE_PATH
init_system tank/test/alt /alt
mkfile data file.txt
capture_file file.txt

assert_file_exists /alt/active/pile-intake/file.txt
assert_not_exists $oldpath/file.txt
