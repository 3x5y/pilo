#!/bin/sh
set -e

# Create repo (simulating client working copy)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cd "$TMPDIR"
git init -q

echo "data" > file.txt
git add file.txt
git commit -m "init" -q

# Create transient state (uncommitted change)
echo "change" >> file.txt

# Run system status
capture_status system-status

[ $STATUS -ne 0 ]
echo "$OUTPUT" | grep -q "transient"
