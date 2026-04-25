#!/bin/sh
set -e

FILE=bad.txt
TMPFILE=/tmp/$FILE

echo bad > $TMPFILE

system-capture $TMPFILE

find /tank/data -name $FILE \
    | assert_not_grep /tank/data/active/pile/
