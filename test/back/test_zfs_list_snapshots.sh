#!/bin/sh
set -eu

pilo snapshot t0

capture_status python3 - <<EOF
from pilo import zfs

entries = zfs.list_snapshot_entries("$TEST_ROOT")

assert entries
names = [e.name for e in entries]
assert any("@t0" in n for n in names)
EOF

assert_command_ok
