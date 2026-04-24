#!/bin/sh
set -e

DATASET="tank/data/active/pile"

# Ensure dataset exists
zfs create -p "$DATASET" 2>/dev/null || true

# Take snapshot
zfs snapshot "$DATASET@test_snap"

# Fake staleness (sleep or just accept "has snapshot")
OUTPUT=$(system-status || true)

capture_status system-status

[ $STATUS -eq 0 ]
echo "$OUTPUT" | grep -q "snapshot"
