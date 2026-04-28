#!/bin/sh
set -e

file=file.txt
canonical=/$PILE/in/$file

mkfile data $file
mtime=$(stat -c%Y $TMP/$file)
capture_file $file
system-ingest-pile
mkintake data $file

system-ingest-pile

# no duplication, no failure
assert_file_exists $canonical
assert_grep data < $canonical
assert_not_exists /$INTAKE/$file
[ $(stat -c%Y $canonical) -eq $mtime ] \
    || fail mtime does not match
