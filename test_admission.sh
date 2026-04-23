#!/bin/sh
set -e

TEST_NAME="admission_completeness"

echo "[TEST] $TEST_NAME"

# --- Setup ---
TMPFILE="/tmp/test_admission.txt"
echo "hello world" > "$TMPFILE"

# --- Action ---
capture "$TMPFILE"

# --- Verify: canonical location ---
if [ ! -f /data/active/pile/test_admission.txt ]; then
    echo "FAIL: file not in canonical location"
    exit 1
fi

# --- Verify: snapshot visibility ---
SNAP="tank/data@admission_test"
zfs snapshot "$SNAP"

if ! zfs diff "$SNAP" | grep -q "test_admission.txt"; then
    echo "FAIL: file not visible in snapshot diff"
    exit 1
fi

echo "PASS: $TEST_NAME"
