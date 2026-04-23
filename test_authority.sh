#!/bin/sh
set -e

TEST_NAME="authority_location"

echo "[TEST] $TEST_NAME"

TMPFILE="/tmp/test_authority.txt"
echo "authority check" > "$TMPFILE"

# --- Action ---
capture "$TMPFILE"

CANONICAL="/data/active/pile/test_authority.txt"

# --- Verify: exists in canonical location ---
if [ ! -f "$CANONICAL" ]; then
    echo "FAIL: canonical file missing"
    exit 1
fi

# --- Verify: no duplicate in intake source ---
if [ -f "$TMPFILE" ]; then
    echo "FAIL: source file still exists (ambiguous authority)"
    exit 1
fi

# --- Verify: canonical path resolves cleanly ---
REALPATH=$(readlink -f "$CANONICAL")

if [ "$REALPATH" != "$CANONICAL" ]; then
    echo "FAIL: canonical path is indirect or ambiguous"
    exit 1
fi

echo "PASS: $TEST_NAME"
