#!/bin/sh
set -e

FILE=bad.txt
TMPFILE=/tmp/$FILE

echo bad > $TMPFILE

system-capture $TMPFILE

# Now assert it did NOT end up somewhere illegal
if find /tank/data -name $FILE | grep -qv "/tank/data/active/pile/"; then
    echo "FAIL: file escaped canonical boundary"
    exit 1
fi
