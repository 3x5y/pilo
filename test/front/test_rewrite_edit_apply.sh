#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo content-ingest

SCRIPT=$(pilo content-reorg-edit --script <<EOF
1	in/b.txt
EOF
)
pilo content-reorg "$SCRIPT"

assert_file_exists "$PILO_PILE_PATH/in/b.txt"
assert_not_exists "$PILO_PILE_PATH/in/a.txt"
