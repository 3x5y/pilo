#!/bin/sh
set -eu

mkfile a a.txt
mkfile b b.txt
mkfile c c.txt

capture_file a.txt
capture_file b.txt
capture_file c.txt

pilo content-ingest

SCRIPT=$(pilo content-reorg-edit --script <<EOF
2	in/x.txt
EOF
)

echo "$SCRIPT" | assert_grep "rm	in/a.txt"
echo "$SCRIPT" | assert_grep "rm	in/c.txt"
echo "$SCRIPT" | assert_grep "mv	in/b.txt	in/x.txt"

pilo rewrite --delete "$SCRIPT"

assert_not_exists "$PILO_PILE_PATH/in/a.txt"
assert_not_exists "$PILO_PILE_PATH/in/b.txt"
assert_not_exists "$PILO_PILE_PATH/in/c.txt"

assert_file_exists "$PILO_PILE_PATH/in/x.txt"
