#!/bin/sh
set -e

SRC="$TEST_ROOT/active/pile"
REPL="$TEST_REPLICA/pile"

# --- create canonical data ---
echo "important" > /tank/data/active/pile/file.txt
zfs snapshot "$SRC@baseline"

# --- replicate using system ---
system-replicate "$SRC" "$REPL"

# --- simulate total loss ---
zfs destroy -r "$TEST_ROOT"

# --- recover using system ---
system-recover-baseline "$REPL" "$SRC" baseline >/dev/null

# --- verify ---
if ! grep -q "important" "/$SRC/.zfs/snapshot/baseline/file.txt"; then
    echo "FAIL: recovery did not restore canonical data"
    exit 1
fi
