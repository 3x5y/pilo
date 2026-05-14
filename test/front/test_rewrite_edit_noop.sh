#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo ingest-pile

SCRIPT=$(pilo rewrite-edit --script <<EOF
1	in/a.txt
EOF
)

[ -z "$SCRIPT" ] || fail "expected empty rewrite script"
