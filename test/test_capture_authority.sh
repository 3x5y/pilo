#!/bin/sh
set -e

FILE=test_authority.txt
TMPFILE=/tmp/$FILE
CANONICAL=/tank/data/active/pile/$FILE

echo authority > $TMPFILE

system-capture $TMPFILE

assert_file_exists $CANONICAL
assert_not_exists $TMPFILE

[ $(readlink -f $CANONICAL) = $CANONICAL ] \
    || fail canonical path is indirect or ambiguous

