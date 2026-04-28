#!/bin/sh
set -e

dir=foo
file=$dir/file.txt

mkintake data $file
system-ingest-pile
# re-upload identical
mkintake data $file

system-ingest-pile

assert_file_exists /$PILE/in/$file
assert_not_exists /$INTAKE/$file
