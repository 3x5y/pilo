#!/bin/sh
set -eu

capture_status python3 - <<EOF
from pilo import zfs

pools = zfs.list_pools()

assert pools
assert pools[0].name == "tank"
EOF

assert_command_ok
