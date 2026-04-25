#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test3.txt

echo valid > $FILE

system-manifest-update

system-manifest-verify
