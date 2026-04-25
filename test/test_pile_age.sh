#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/old_file.txt

mkdir -p $PILE
echo data > $FILE

touch -d '2 hours ago' $FILE

export CONFIG_PILE_MAX_AGE=60
capture_status system-status

[ $STATUS -ne 0 ] || fail status returned zero
echo "$OUTPUT" | assert_grep pile:
echo "$OUTPUT" | assert_grep old_file.txt
