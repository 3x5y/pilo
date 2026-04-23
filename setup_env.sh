#!/bin/sh
set -e

echo "[SETUP] Creating test environment"

# Clean up if previous run was sloppy
zpool destroy -f tank 2>/dev/null || true
losetup -D 2>/dev/null || true
rm -f /tmp/vdev* 2>/dev/null || true

# Create loopback devices (fast, disposable)
truncate -s 2G /tmp/vdev1
truncate -s 2G /tmp/vdev2

LOOP1=$(losetup --show -f /tmp/vdev1)
LOOP2=$(losetup --show -f /tmp/vdev2)

# Create pool
zpool create tank "$LOOP1"

# Create dataset structure
zfs create -p tank/data/active/pile
zfs create -p tank/data/archive
zfs create -p tank/data/spool
zfs create -p tank/data/stash

echo "[SETUP] Done"
