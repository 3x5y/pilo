#!/bin/sh
set -e

FILE="/tank/data/active/pile/recovery_test.txt"

# --- Setup ---
echo "recover me" > "$FILE"

SNAP="tank/data/active/pile@recovery_test"
zfs snapshot "$SNAP"

# --- Action: destroy file ---
rm "$FILE"

if [ -f "$FILE" ]; then
    echo "FAIL: file not deleted"
    exit 1
fi

# --- Action: rollback ---
zfs rollback "$SNAP"

# --- Verify ---
if [ ! -f "$FILE" ]; then
    echo "FAIL: file not restored after rollback"
    exit 1
fi
