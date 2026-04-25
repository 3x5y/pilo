#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/new_file.txt

mkdir -p $PILE
echo data > $FILE

capture_status system-status pile

[ $STATUS -eq 0 ] || fail expected no pile age warning
