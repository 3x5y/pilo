#!/bin/sh
set -e

# Create repo (simulating client working copy)
mkdir -p /tmp/test_repo

trap 'rm -rf /tmp/test_repo' EXIT

cd /tmp/test_repo
git init -q

echo "data" > file.txt
git add file.txt
git commit -m "init" -q

# Create transient state (uncommitted change)
echo "change" >> file.txt

# Run system status
OUTPUT=$(system-status || true)

echo "$OUTPUT" | grep -q "transient"
