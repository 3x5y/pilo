#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file

assert_file_exists /$INTAKE/$file
assert_not_exists /$PILE/$file
# client copy retained
assert_file_exists $TMP/$file
