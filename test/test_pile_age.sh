#!/bin/sh
set -e

PILE="/tank/data/active/pile"
FILE="$PILE/old_file.txt"

mkdir -p "$PILE"
echo "data" > "$FILE"

# Backdate file (2 days ago)
touch -d "2 days ago" "$FILE"

# Run system status
capture_status system-status

[ $STATUS -ne 0 ]
echo "$OUTPUT" | grep -q "pile"
echo "$OUTPUT" | grep -q "old_file.txt"
