#!/bin/sh
set -e

FILE=file.txt
INTAKE=/tank/data/active/pile-intake/$FILE
CANONICAL=/tank/data/active/pile-readonly/$FILE

echo data > /tmp/$FILE
mtime=$(stat -c%Y /tmp/$FILE)
system-capture /tmp/$FILE
system-ingest-pile
echo data > $INTAKE

system-ingest-pile

# no duplication, no failure
assert_file_exists $CANONICAL
assert_grep data < $CANONICAL
assert_not_exists $INTAKE
[ $(stat -c%Y $CANONICAL) -eq $mtime ] \
    || fail mtime does not match
