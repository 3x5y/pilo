#!/bin/sh
set -e

FILE=file.txt
INTAKE=/tank/data/active/pile-intake/$FILE
CANONICAL=/tank/data/active/pile-readonly/in/$FILE

echo data > /tmp/$FILE
system-capture /tmp/$FILE

system-ingest-pile

assert_file_exists $CANONICAL
assert_not_exists $INTAKE
[ $(readlink -f $CANONICAL) = $CANONICAL ] \
    || fail canonical path is indirect or ambiguous
