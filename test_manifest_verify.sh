#!/bin/sh
set -e

PILE="/tank/data/active/pile"
FILE="$PILE/test3.txt"

echo "original" > "$FILE"

system-manifest-update

# corrupt file
echo "corruption" > "$FILE"

set +e
OUTPUT=$(system-manifest-verify 2>&1)
STATUS=$?
set -e

[ $STATUS -ne 0 ]
echo "$OUTPUT" | grep -q "mismatch"
