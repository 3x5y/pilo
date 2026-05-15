#!/bin/sh
set -eu

capture_status python3 - <<EOF
from pilo import zfs

entries = zfs.list_datasets("$TEST_ROOT")

names = [e.name for e in entries]

assert "$ADMIN" in names
assert "$PILE" in names
EOF

assert_command_ok
