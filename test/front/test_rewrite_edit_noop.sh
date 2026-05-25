#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo content-ingest

SCRIPT=$(pilo content-reorg-edit --script <<EOF
1	in/a.txt
EOF
)

[ -z "$SCRIPT" ] || fail "expected empty rewrite script"
