#!/bin/sh
set -e

PILE="/tank/data/active/pile"
FILE="$PILE/old_file.txt"

mkdir -p "$PILE"
echo "data" > "$FILE"

# Backdate file (2 days ago)
touch -d "2 days ago" "$FILE"

# Run system status
OUTPUT=$(system-status || true)

echo "$OUTPUT" | grep -q "pile"
echo "$OUTPUT" | grep -q "old_file.txt"
