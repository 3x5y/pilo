#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/old_file.txt

mkdir -p $PILE
echo data > $FILE

touch -d '2 days ago' $FILE

capture_status system-status

[ $STATUS -ne 0 ] || fail status returned zero
echo $OUTPUT | assert_grep pile
echo $OUTPUT | assert_grep old_file.txt
