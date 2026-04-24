#!/bin/sh
set -e

PILE="/tank/data/active/pile"
FILE="$PILE/test.txt"

echo "hello" > "$FILE"

system-manifest-update

grep -q "test.txt" "$PILE/.manifest"
