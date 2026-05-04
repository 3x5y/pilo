#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo ingest-pile

SCRIPT=$(pilo rewrite-edit --script <<EOF
in/b.txt
EOF
)
pilo rewrite "$SCRIPT"

assert_file_exists "$PILO_PILE_PATH/in/b.txt"
assert_not_exists "$PILO_PILE_PATH/in/a.txt"
