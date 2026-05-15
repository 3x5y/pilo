#!/bin/sh
set -eu

python3 - <<EOF
from pilo import zfs

assert zfs.get_role("$ADMIN") is None
EOF
