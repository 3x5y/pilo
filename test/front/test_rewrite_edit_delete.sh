#!/bin/sh
set -eu

mkfile a a.txt
mkfile b b.txt

capture_file a.txt
capture_file b.txt

pilo content-ingest

SCRIPT=$(pilo content-reorg-edit --script <<EOF
2	in/b.txt
EOF
)

echo "$SCRIPT" | assert_grep "rm	in/a.txt"

pilo rewrite --delete "$SCRIPT"

assert_not_exists "$PILO_PILE_PATH/in/a.txt"
assert_file_exists "$PILO_PILE_PATH/in/b.txt"
