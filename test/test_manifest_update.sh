#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test2.txt

echo data > $FILE

system-manifest-update

cp $PILE/.manifest /tmp/manifest_before
echo more >> $FILE

system-manifest-update

assert_grep test2.txt < $PILE/.manifest
