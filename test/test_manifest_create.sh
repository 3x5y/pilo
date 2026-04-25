#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test.txt

echo hello > $FILE

system-manifest-update

assert_grep test.txt < $PILE/.manifest
