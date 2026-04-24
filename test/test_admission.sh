#!/bin/sh
set -e

# --- Setup ---
TMPFILE="/tmp/test_admission.txt"
echo "hello world" > "$TMPFILE"

# --- Action ---
system-capture "$TMPFILE"

# --- Verify: canonical location ---
if [ ! -f /tank/data/active/pile/test_admission.txt ]; then
    echo "FAIL: file not in canonical location"
    exit 1
fi

# --- Verify: snapshot visibility ---
SNAP="tank/data/active/pile@after_admission"
zfs snapshot "$SNAP"

if [ ! -f "/tank/data/active/pile/.zfs/snapshot/after_admission/test_admission.txt" ]; then
    echo "FAIL: file not present in snapshot"
    exit 1
fi
