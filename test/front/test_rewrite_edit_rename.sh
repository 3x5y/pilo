#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo ingest-pile

SCRIPT=$(pilo rewrite-edit --script <<EOF
1	in/b.txt
EOF
)

# NB tab chars
echo "$SCRIPT" | assert_grep "mv	in/a.txt	in/b.txt"
