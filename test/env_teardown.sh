#!/bin/sh
set -e

echo "[TEARDOWN] Destroying test environment"

zpool destroy -f tank 2>/dev/null || true
losetup -D 2>/dev/null || true
rm -f /tmp/vdev* 2>/dev/null || true

echo "[TEARDOWN] Done"
