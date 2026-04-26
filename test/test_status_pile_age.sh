#!/bin/sh
set -e

FILE=old_file.txt

echo data > /tmp/$FILE
touch -d '2 hours ago' /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

export CONFIG_PILE_MAX_AGE=60
capture_status system-status pile

[ $STATUS -ne 0 ] || fail status returned zero
echo "$OUTPUT" | assert_grep pile:
echo "$OUTPUT" | assert_grep old_file.txt
