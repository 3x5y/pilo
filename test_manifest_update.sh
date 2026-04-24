#!/bin/sh
set -e

PILE="/tank/data/active/pile"
FILE="$PILE/test2.txt"

echo "data" > "$FILE"

system-manifest-update

# capture manifest state
cp "$PILE/.manifest" /tmp/manifest_before

# modify unrelated file
echo "more" >> "$FILE"

system-manifest-update

# ensure manifest updated but not rebuilt blindly
grep -q "test2.txt" "$PILE/.manifest"
