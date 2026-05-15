#!/bin/sh
set -eu

python3 - <<EOF
from pilo import zfs

zfs.set_role("$TEST_ROOT", zfs.ROLE_PRIMARY)

assert zfs.get_role("$TEST_ROOT") == zfs.ROLE_PRIMARY
EOF
