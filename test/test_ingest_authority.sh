#!/bin/sh
set -e

file=file.txt
canonical=/$PILE/in/$file

mkfile data $file
capture_file $file
system-ingest-pile

assert_file_exists $canonical
assert_not_exists /$INTAKE/$file
[ $(readlink -f $canonical) = $canonical ] \
    || fail canonical path is indirect or ambiguous
